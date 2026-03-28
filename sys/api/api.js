// ==========================================
// FILE: /api/server.js - Main Server Entry Point
// ==========================================
import express from 'express';
import cors from 'cors';
import helmet from 'helmet';
import compression from 'compression';
import rateLimit from 'express-rate-limit';
import dotenv from 'dotenv';
import { errorHandler } from './middleware/errorHandler.js';
import { logger } from './utils/logger.js';
import { connectDB } from './config/database.js';
import routes from './routes/index.js';

// Load environment variables
dotenv.config();

// Create Express app
const app = express();
const PORT = process.env.PORT || 3000;

// ==========================================
// Middleware Configuration
// ==========================================
app.use(helmet()); // Security headers
app.use(cors({
  origin: process.env.ALLOWED_ORIGINS?.split(',') || '*',
  credentials: true
}));
app.use(compression()); // Compress responses
app.use(express.json({ limit: '10mb' }));
app.use(express.urlencoded({ extended: true }));

// Rate limiting
const limiter = rateLimit({
  windowMs: 15 * 60 * 1000, // 15 minutes
  max: 100, // Limit each IP to 100 requests per windowMs
  message: 'Too many requests from this IP, please try again later.'
});
app.use('/api/', limiter);

// Request logging middleware
app.use((req, res, next) => {
  logger.info(`${req.method} ${req.path}`, {
    ip: req.ip,
    userAgent: req.get('User-Agent')
  });
  next();
});

// API Routes
app.use('/api', routes);

// Health check endpoint
app.get('/health', (req, res) => {
  res.json({ 
    status: 'healthy', 
    timestamp: new Date().toISOString(),
    uptime: process.uptime()
  });
});

// Error handling middleware (must be last)
app.use(errorHandler);

// Start server
const startServer = async () => {
  try {
    // Connect to database
    await connectDB();
    
    app.listen(PORT, () => {
      logger.info(`Server running on port ${PORT} in ${process.env.NODE_ENV} mode`);
    });
  } catch (error) {
    logger.error('Failed to start server:', error);
    process.exit(1);
  }
};

startServer();

// ==========================================
// FILE: /api/config/database.js - Database Configuration
// ==========================================
import mongoose from 'mongoose';
import { logger } from '../utils/logger.js';

export const connectDB = async () => {
  try {
    const conn = await mongoose.connect(process.env.MONGODB_URI || 'mongodb://localhost:27017/api_db', {
      useNewUrlParser: true,
      useUnifiedTopology: true,
    });
    
    logger.info(`MongoDB Connected: ${conn.connection.host}`);
    
    // Handle connection events
    mongoose.connection.on('error', (err) => {
      logger.error('MongoDB connection error:', err);
    });
    
    mongoose.connection.on('disconnected', () => {
      logger.warn('MongoDB disconnected');
    });
    
  } catch (error) {
    logger.error('Database connection failed:', error);
    throw error;
  }
};

// ==========================================
// FILE: /api/routes/index.js - Main Router
// ==========================================
import { Router } from 'express';
import userRoutes from './users.js';
import authRoutes from './auth.js';
import productRoutes from './products.js';

const router = Router();

// API version prefix
const API_VERSION = '/v1';

// Mount route modules
router.use(`${API_VERSION}/auth`, authRoutes);
router.use(`${API_VERSION}/users`, userRoutes);
router.use(`${API_VERSION}/products`, productRoutes);

// API documentation endpoint
router.get('/', (req, res) => {
  res.json({
    message: 'API is running',
    version: '1.0.0',
    endpoints: {
      auth: `${API_VERSION}/auth`,
      users: `${API_VERSION}/users`,
      products: `${API_VERSION}/products`,
    }
  });
});

export default router;

// ==========================================
// FILE: /api/routes/auth.js - Authentication Routes
// ==========================================
import { Router } from 'express';
import { body } from 'express-validator';
import { authController } from '../controllers/authController.js';
import { validateRequest } from '../middleware/validateRequest.js';

const router = Router();

// Register new user
router.post('/register', [
  body('email').isEmail().normalizeEmail(),
  body('password').isLength({ min: 8 }).withMessage('Password must be at least 8 characters'),
  body('name').trim().notEmpty(),
  validateRequest
], authController.register);

// Login
router.post('/login', [
  body('email').isEmail().normalizeEmail(),
  body('password').notEmpty(),
  validateRequest
], authController.login);

// Refresh token
router.post('/refresh', authController.refreshToken);

// Logout
router.post('/logout', authController.logout);

// Password reset request
router.post('/forgot-password', [
  body('email').isEmail().normalizeEmail(),
  validateRequest
], authController.forgotPassword);

// Reset password
router.post('/reset-password', [
  body('token').notEmpty(),
  body('password').isLength({ min: 8 }),
  validateRequest
], authController.resetPassword);

export default router;

// ==========================================
// FILE: /api/routes/users.js - User Routes
// ==========================================
import { Router } from 'express';
import { body, param, query } from 'express-validator';
import { userController } from '../controllers/userController.js';
import { authenticate } from '../middleware/authenticate.js';
import { authorize } from '../middleware/authorize.js';
import { validateRequest } from '../middleware/validateRequest.js';
import { cache } from '../middleware/cache.js';

const router = Router();

// Get all users (admin only) with pagination
router.get('/', 
  authenticate, 
  authorize(['admin']),
  query('page').optional().isInt({ min: 1 }),
  query('limit').optional().isInt({ min: 1, max: 100 }),
  query('sort').optional().isIn(['name', 'email', 'createdAt']),
  validateRequest,
  cache(60), // Cache for 60 seconds
  userController.getAllUsers
);

// Get current user profile
router.get('/profile', authenticate, userController.getProfile);

// Get user by ID
router.get('/:id', 
  authenticate,
  param('id').isMongoId(),
  validateRequest,
  userController.getUserById
);

// Update user profile
router.patch('/profile', 
  authenticate,
  body('name').optional().trim().notEmpty(),
  body('bio').optional().trim(),
  validateRequest,
  userController.updateProfile
);

// Update user (admin only)
router.patch('/:id',
  authenticate,
  authorize(['admin']),
  param('id').isMongoId(),
  validateRequest,
  userController.updateUser
);

// Delete user (admin only)
router.delete('/:id',
  authenticate,
  authorize(['admin']),
  param('id').isMongoId(),
  validateRequest,
  userController.deleteUser
);

export default router;

// ==========================================
// FILE: /api/controllers/authController.js - Auth Controller
// ==========================================
import bcrypt from 'bcryptjs';
import jwt from 'jsonwebtoken';
import { User } from '../models/User.js';
import { ApiError } from '../utils/ApiError.js';
import { ApiResponse } from '../utils/ApiResponse.js';
import { generateTokens } from '../utils/tokenUtils.js';
import { sendEmail } from '../services/emailService.js';

class AuthController {
  async register(req, res, next) {
    try {
      const { email, password, name } = req.body;
      
      // Check if user exists
      const existingUser = await User.findOne({ email });
      if (existingUser) {
        throw new ApiError(400, 'User already exists');
      }
      
      // Hash password
      const hashedPassword = await bcrypt.hash(password, 12);
      
      // Create user
      const user = await User.create({
        email,
        password: hashedPassword,
        name
      });
      
      // Generate tokens
      const { accessToken, refreshToken } = generateTokens(user._id);
      
      // Save refresh token to database
      user.refreshTokens.push({
        token: refreshToken,
        createdAt: new Date()
      });
      await user.save();
      
      // Send welcome email
      await sendEmail(user.email, 'welcome', { name: user.name });
      
      res.status(201).json(new ApiResponse(201, {
        user: user.toJSON(),
        accessToken,
        refreshToken
      }, 'User registered successfully'));
      
    } catch (error) {
      next(error);
    }
  }
  
  async login(req, res, next) {
    try {
      const { email, password } = req.body;
      
      // Find user
      const user = await User.findOne({ email }).select('+password');
      if (!user) {
        throw new ApiError(401, 'Invalid credentials');
      }
      
      // Check password
      const isPasswordValid = await bcrypt.compare(password, user.password);
      if (!isPasswordValid) {
        throw new ApiError(401, 'Invalid credentials');
      }
      
      // Update last login
      user.lastLogin = new Date();
      
      // Generate tokens
      const { accessToken, refreshToken } = generateTokens(user._id);
      
      // Save refresh token
      user.refreshTokens.push({
        token: refreshToken,
        createdAt: new Date()
      });
      
      // Clean old refresh tokens (keep last 5)
      if (user.refreshTokens.length > 5) {
        user.refreshTokens = user.refreshTokens.slice(-5);
      }
      
      await user.save();
      
      res.json(new ApiResponse(200, {
        user: user.toJSON(),
        accessToken,
        refreshToken
      }, 'Login successful'));
      
    } catch (error) {
      next(error);
    }
  }
  
  async refreshToken(req, res, next) {
    try {
      const { refreshToken } = req.body;
      
      if (!refreshToken) {
        throw new ApiError(401, 'Refresh token required');
      }
      
      // Verify refresh token
      const decoded = jwt.verify(refreshToken, process.env.REFRESH_TOKEN_SECRET);
      
      // Find user and check if refresh token exists
      const user = await User.findById(decoded.userId);
      if (!user) {
        throw new ApiError(401, 'Invalid refresh token');
      }
      
      const tokenExists = user.refreshTokens.some(t => t.token === refreshToken);
      if (!tokenExists) {
        throw new ApiError(401, 'Invalid refresh token');
      }
      
      // Generate new tokens
      const tokens = generateTokens(user._id);
      
      // Replace old refresh token with new one
      user.refreshTokens = user.refreshTokens.filter(t => t.token !== refreshToken);
      user.refreshTokens.push({
        token: tokens.refreshToken,
        createdAt: new Date()
      });
      
      await user.save();
      
      res.json(new ApiResponse(200, tokens, 'Tokens refreshed'));
      
    } catch (error) {
      next(error);
    }
  }
  
  async logout(req, res, next) {
    try {
      const { refreshToken } = req.body;
      
      if (refreshToken) {
        // Find user and remove refresh token
        const decoded = jwt.verify(refreshToken, process.env.REFRESH_TOKEN_SECRET, {
          ignoreExpiration: true
        });
        
        const user = await User.findById(decoded.userId);
        if (user) {
          user.refreshTokens = user.refreshTokens.filter(t => t.token !== refreshToken);
          await user.save();
        }
      }
      
      res.json(new ApiResponse(200, null, 'Logged out successfully'));
      
    } catch (error) {
      next(error);
    }
  }
  
  async forgotPassword(req, res, next) {
    try {
      const { email } = req.body;
      
      const user = await User.findOne({ email });
      if (!user) {
        // Don't reveal if user exists
        res.json(new ApiResponse(200, null, 'If user exists, reset email has been sent'));
        return;
      }
      
      // Generate reset token
      const resetToken = jwt.sign(
        { userId: user._id, purpose: 'password-reset' },
        process.env.JWT_SECRET,
        { expiresIn: '1h' }
      );
      
      // Save reset token to user
      user.passwordResetToken = resetToken;
      user.passwordResetExpires = new Date(Date.now() + 3600000); // 1 hour
      await user.save();
      
      // Send reset email
      await sendEmail(user.email, 'password-reset', {
        name: user.name,
        resetLink: `${process.env.FRONTEND_URL}/reset-password?token=${resetToken}`
      });
      
      res.json(new ApiResponse(200, null, 'If user exists, reset email has been sent'));
      
    } catch (error) {
      next(error);
    }
  }
  
  async resetPassword(req, res, next) {
    try {
      const { token, password } = req.body;
      
      // Verify token
      const decoded = jwt.verify(token, process.env.JWT_SECRET);
      
      if (decoded.purpose !== 'password-reset') {
        throw new ApiError(400, 'Invalid token');
      }
      
      // Find user
      const user = await User.findOne({
        _id: decoded.userId,
        passwordResetToken: token,
        passwordResetExpires: { $gt: Date.now() }
      });
      
      if (!user) {
        throw new ApiError(400, 'Invalid or expired token');
      }
      
      // Update password
      user.password = await bcrypt.hash(password, 12);
      user.passwordResetToken = undefined;
      user.passwordResetExpires = undefined;
      
      // Invalidate all refresh tokens
      user.refreshTokens = [];
      
      await user.save();
      
      // Send confirmation email
      await sendEmail(user.email, 'password-reset-success', { name: user.name });
      
      res.json(new ApiResponse(200, null, 'Password reset successful'));
      
    } catch (error) {
      next(error);
    }
  }
}

export const authController = new AuthController();

// ==========================================
// FILE: /api/models/User.js - User Model
// ==========================================
import mongoose from 'mongoose';

const userSchema = new mongoose.Schema({
  email: {
    type: String,
    required: true,
    unique: true,
    lowercase: true,
    trim: true,
    index: true
  },
  password: {
    type: String,
    required: true,
    select: false
  },
  name: {
    type: String,
    required: true,
    trim: true
  },
  bio: {
    type: String,
    maxlength: 500
  },
  avatar: {
    type: String,
    default: null
  },
  role: {
    type: String,
    enum: ['user', 'admin', 'moderator'],
    default: 'user'
  },
  isActive: {
    type: Boolean,
    default: true
  },
  isVerified: {
    type: Boolean,
    default: false
  },
  verificationToken: String,
  passwordResetToken: String,
  passwordResetExpires: Date,
  refreshTokens: [{
    token: String,
    createdAt: {
      type: Date,
      default: Date.now,
      expires: 604800 // 7 days
    }
  }],
  lastLogin: Date,
  loginAttempts: {
    type: Number,
    default: 0
  },
  lockUntil: Date
}, {
  timestamps: true,
  toJSON: {
    transform(doc, ret) {
      delete ret.password;
      delete ret.refreshTokens;
      delete ret.passwordResetToken;
      delete ret.passwordResetExpires;
      delete ret.verificationToken;
      delete ret.__v;
      return ret;
    }
  }
});

// Indexes for better query performance
userSchema.index({ createdAt: -1 });
userSchema.index({ role: 1, isActive: 1 });

// Virtual for account age
userSchema.virtual('accountAge').get(function() {
  return Math.floor((Date.now() - this.createdAt) / (1000 * 60 * 60 * 24));
});

// Method to check if account is locked
userSchema.methods.isLocked = function() {
  return !!(this.lockUntil && this.lockUntil > Date.now());
};

export const User = mongoose.model('User', userSchema);

// ==========================================
// FILE: /api/middleware/authenticate.js - Authentication Middleware
// ==========================================
import jwt from 'jsonwebtoken';
import { User } from '../models/User.js';
import { ApiError } from '../utils/ApiError.js';

export const authenticate = async (req, res, next) => {
  try {
    const token = req.header('Authorization')?.replace('Bearer ', '');
    
    if (!token) {
      throw new ApiError(401, 'Authentication required');
    }
    
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    const user = await User.findById(decoded.userId).select('-password -refreshTokens');
    
    if (!user) {
      throw new ApiError(401, 'User not found');
    }
    
    if (!user.isActive) {
      throw new ApiError(403, 'Account is deactivated');
    }
    
    req.user = user;
    req.userId = user._id;
    
    next();
  } catch (error) {
    if (error.name === 'JsonWebTokenError') {
      next(new ApiError(401, 'Invalid token'));
    } else if (error.name === 'TokenExpiredError') {
      next(new ApiError(401, 'Token expired'));
    } else {
      next(error);
    }
  }
};

// ==========================================
// FILE: /api/middleware/errorHandler.js - Error Handling Middleware
// ==========================================
import { ApiError } from '../utils/ApiError.js';
import { logger } from '../utils/logger.js';

export const errorHandler = (err, req, res, next) => {
  let error = err;
  
  // Handle Mongoose errors
  if (err.name === 'CastError') {
    error = new ApiError(400, 'Invalid ID format');
  } else if (err.code === 11000) {
    const field = Object.keys(err.keyPattern)[0];
    error = new ApiError(400, `${field} already exists`);
  } else if (err.name === 'ValidationError') {
    const messages = Object.values(err.errors).map(e => e.message);
    error = new ApiError(400, messages.join(', '));
  }
  
  // Log error
  logger.error({
    message: error.message,
    stack: error.stack,
    statusCode: error.statusCode || 500,
    path: req.path,
    method: req.method,
    ip: req.ip
  });
  
  // Send error response
  res.status(error.statusCode || 500).json({
    success: false,
    message: error.message || 'Internal server error',
    ...(process.env.NODE_ENV === 'development' && { stack: error.stack })
  });
};

// ==========================================
// FILE: /api/utils/ApiResponse.js - Standard API Response
// ==========================================
export class ApiResponse {
  constructor(statusCode, data = null, message = 'Success') {
    this.success = statusCode < 400;
    this.statusCode = statusCode;
    this.message = message;
    this.data = data;
    this.timestamp = new Date().toISOString();
  }
}

// ==========================================
// FILE: /api/utils/ApiError.js - Custom Error Class
// ==========================================
export class ApiError extends Error {
  constructor(statusCode, message = 'Something went wrong', errors = []) {
    super(message);
    this.statusCode = statusCode;
    this.message = message;
    this.errors = errors;
    this.success = false;
    
    Error.captureStackTrace(this, this.constructor);
  }
}

// ==========================================
// FILE: /api/.env.example - Environment Variables Template
// ==========================================
`# Server Configuration
NODE_ENV=development
PORT=3000

# Database
MONGODB_URI=mongodb://localhost:27017/api_db

# JWT Secrets
JWT_SECRET=your-super-secret-jwt-key-change-this
REFRESH_TOKEN_SECRET=your-refresh-token-secret-change-this

# Security
ALLOWED_ORIGINS=http://localhost:3000,http://localhost:5173

# Email Configuration
EMAIL_HOST=smtp.gmail.com
EMAIL_PORT=587
EMAIL_USER=your-email@gmail.com
EMAIL_PASS=your-app-password

# Frontend URL
FRONTEND_URL=http://localhost:3000

# Redis (for caching)
REDIS_URL=redis://localhost:6379

# Rate Limiting
RATE_LIMIT_WINDOW_MS=900000
RATE_LIMIT_MAX_REQUESTS=100

# File Upload
MAX_FILE_SIZE=10485760
UPLOAD_DIR=./uploads`;

// ==========================================
// FILE: /api/package.json - Dependencies
// ==========================================
const packageJson = `{
  "name": "modern-api",
  "version": "1.0.0",
  "type": "module",
  "main": "server.js",
  "scripts": {
    "start": "node server.js",
    "dev": "nodemon server.js",
    "test": "jest",
    "lint": "eslint ."
  },
  "dependencies": {
    "express": "^4.19.2",
    "mongoose": "^8.5.0",
    "jsonwebtoken": "^9.0.2",
    "bcryptjs": "^2.4.3",
    "dotenv": "^16.4.5",
    "cors": "^2.8.5",
    "helmet": "^7.1.0",
    "express-rate-limit": "^7.3.1",
    "express-validator": "^7.1.0",
    "compression": "^1.7.4",
    "winston": "^3.13.0",
    "nodemailer": "^6.9.14",
    "redis": "^4.6.15",
    "multer": "^1.4.5-lts.1",
    "sharp": "^0.33.4"
  },
  "devDependencies": {
    "nodemon": "^3.1.4",
    "eslint": "^9.7.0",
    "jest": "^29.7.0",
    "supertest": "^7.0.0"
  }
}`;

console.log('Package.json content:', packageJson);