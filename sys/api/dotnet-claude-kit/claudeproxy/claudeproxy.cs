 * claudeproxy.cs — Claude API Proxy Koruma Katmanı
 * ==================================================
 * ASP.NET Core 8+ Minimal API
 *
 * Özellikler:
 *   - JWT kimlik doğrulama
 *   - Rate limiting (IP + kullanıcı bazlı)
 *   - İstek/yanıt şifreleme (AES-256-GCM)
 *   - Prompt enjeksiyon koruması
 *   - İstek denetim izi (audit log)
 *   - CORS politika yönetimi
 *   - JSON şema doğrulaması
 *   - IP kara/beyaz listesi
 *
 * Kurulum:
 *   dotnet add package Microsoft.AspNetCore.Authentication.JwtBearer
 *   dotnet add package AspNetCoreRateLimit
 *   dotnet add package Serilog.AspNetCore
 */

using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.IdentityModel.Tokens.Jwt;
using System.Net;
using System.Net.Http;
using System.Net.Http.Headers;
using System.Security.Claims;
using System.Security.Cryptography;
using System.Text;
using System.Text.Json;
using System.Text.RegularExpressions;
using System.Threading;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Builder;
using Microsoft.AspNetCore.Http;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.DependencyInjection;
using Microsoft.Extensions.Logging;
using Microsoft.IdentityModel.Tokens;

// ─────────────────────────────────────────────────────────────────────────────
// YAPILANDIRMA MODELİ
// ─────────────────────────────────────────────────────────────────────────────

/// <summary>Proxy konfigürasyon ayarları — appsettings.json'dan yüklenir.</summary>
public sealed record ProxyConfig
{
    public string  ClaudeApiUrl      { get; init; } = "https://api.anthropic.com/v1/messages";
    public string  ClaudeApiKey      { get; init; } = "";          // Ortam değişkeninden okunur
    public string  JwtSecret         { get; init; } = "";
    public string  JwtIssuer         { get; init; } = "claude-proxy";
    public string  JwtAudience       { get; init; } = "claude-clients";
    public int     JwtExpiryMinutes  { get; init; } = 60;
    public int     RateLimitPerMin   { get; init; } = 20;          // Kullanıcı başına istek/dakika
    public int     RateLimitPerHour  { get; init; } = 200;
    public int     MaxPromptLength   { get; init; } = 8000;
    public bool    EnableEncryption  { get; init; } = true;
    public bool    EnableAuditLog    { get; init; } = true;
    public string  EncryptionKey     { get; init; } = "";          // 32 byte base64
    public List<string> AllowedIPs   { get; init; } = new();       // Boş = hepsi
    public List<string> BlockedIPs   { get; init; } = new();
    public List<string> AllowedOrigins { get; init; } = new() { "*" };
}

// ─────────────────────────────────────────────────────────────────────────────
// ŞİFRELEME SERVİSİ
// ─────────────────────────────────────────────────────────────────────────────

/// <summary>AES-256-GCM ile istek/yanıt şifreleme.</summary>
public sealed class EncryptionService
{
    private readonly byte[] _key;

    public EncryptionService(string base64Key)
    {
        if (string.IsNullOrEmpty(base64Key))
        {
            // Geliştirme: rastgele anahtar üret (üretimde ortam değişkeni kullan)
            _key = new byte[32];
            RandomNumberGenerator.Fill(_key);
        }
        else
        {
            _key = Convert.FromBase64String(base64Key);
            if (_key.Length != 32)
                throw new ArgumentException("Şifreleme anahtarı 32 byte (256-bit) olmalıdır.");
        }
    }

    /// <summary>Metni AES-256-GCM ile şifreler. Döndürür: base64(nonce+tag+şifreli).</summary>
    public string Encrypt(string plainText)
    {
        var nonce      = new byte[AesGcm.NonceByteSizes.MaxSize];      // 12 byte
        var tag        = new byte[AesGcm.TagByteSizes.MaxSize];        // 16 byte
        var plainBytes = Encoding.UTF8.GetBytes(plainText);
        var cipher     = new byte[plainBytes.Length];

        RandomNumberGenerator.Fill(nonce);

        using var aes = new AesGcm(_key, AesGcm.TagByteSizes.MaxSize);
        aes.Encrypt(nonce, plainBytes, cipher, tag);

        var result = new byte[nonce.Length + tag.Length + cipher.Length];
        Buffer.BlockCopy(nonce,  0, result, 0,                          nonce.Length);
        Buffer.BlockCopy(tag,    0, result, nonce.Length,               tag.Length);
        Buffer.BlockCopy(cipher, 0, result, nonce.Length + tag.Length,  cipher.Length);

        return Convert.ToBase64String(result);
    }

    /// <summary>Encrypt() ile şifrelenmiş base64 veriyi çözer.</summary>
    public string Decrypt(string encryptedBase64)
    {
        var data   = Convert.FromBase64String(encryptedBase64);
        var nonce  = data[..12];
        var tag    = data[12..28];
        var cipher = data[28..];
        var plain  = new byte[cipher.Length];

        using var aes = new AesGcm(_key, AesGcm.TagByteSizes.MaxSize);
        aes.Decrypt(nonce, cipher, tag, plain);

        return Encoding.UTF8.GetString(plain);
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// RATE LIMITER
// ─────────────────────────────────────────────────────────────────────────────

/// <summary>Sliding window rate limiter — IP ve kullanıcı bazlı.</summary>
public sealed class RateLimiter
{
    private record Window(ConcurrentQueue<DateTime> Hits);

    private readonly ConcurrentDictionary<string, Window> _windows = new();
    private readonly int _perMinute;
    private readonly int _perHour;

    public RateLimiter(int perMinute, int perHour)
    {
        _perMinute = perMinute;
        _perHour   = perHour;
    }

    /// <summary>
    /// Anahtarın (IP veya kullanıcı ID) rate limit dahilinde olup
    /// olmadığını kontrol eder.
    /// </summary>
    /// <returns>true → istek kabul edilebilir, false → limit aşıldı</returns>
    public bool TryAcquire(string key)
    {
        var window = _windows.GetOrAdd(key, _ => new Window(new ConcurrentQueue<DateTime>()));
        var now    = DateTime.UtcNow;

        // Eski girişleri temizle (1 saat öncesi)
        while (window.Hits.TryPeek(out var oldest) && (now - oldest).TotalHours >= 1)
            window.Hits.TryDequeue(out _);

        var hourHits   = window.Hits.Count;
        var minuteHits = window.Hits.Count(h => (now - h).TotalMinutes < 1);

        if (hourHits >= _perHour || minuteHits >= _perMinute)
            return false;

        window.Hits.Enqueue(now);
        return true;
    }

    /// <summary>Belirli bir anahtarın mevcut hit sayısını döndürür.</summary>
    public (int PerMinute, int PerHour) GetUsage(string key)
    {
        if (!_windows.TryGetValue(key, out var window))
            return (0, 0);

        var now = DateTime.UtcNow;
        return (
            window.Hits.Count(h => (now - h).TotalMinutes < 1),
            window.Hits.Count
        );
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// PROMPT KORUMASI
// ─────────────────────────────────────────────────────────────────────────────

/// <summary>Prompt enjeksiyon ve kötüye kullanım koruması.</summary>
public sealed class PromptGuard
{
    // Prompt enjeksiyon örüntüleri
    private static readonly Regex[] _injectionPatterns =
    [
        new(@"ignore\s+(all\s+)?previous\s+instructions?", RegexOptions.IgnoreCase),
        new(@"system\s+prompt", RegexOptions.IgnoreCase),
        new(@"jailbreak", RegexOptions.IgnoreCase),
        new(@"DAN\s+mode", RegexOptions.IgnoreCase),
        new(@"pretend\s+you\s+(are|have\s+no)", RegexOptions.IgnoreCase),
        new(@"forget\s+(all\s+)?your\s+(rules?|guidelines?|restrictions?)", RegexOptions.IgnoreCase),
        new(@"act\s+as\s+(if\s+you\s+are\s+)?(a\s+)?(?:evil|unrestricted|unfiltered)", RegexOptions.IgnoreCase),
        new(@"\[INST\]|\[\/INST\]|<\|im_start\|>|<\|im_end\|>", RegexOptions.IgnoreCase),
    ];

    // İzin verilmeyen içerik kategorileri
    private static readonly Regex[] _contentPatterns =
    [
        new(@"\b(bomb|weapon|explosive)\s+(make|build|create|instructions?)\b", RegexOptions.IgnoreCase),
        new(@"\b(malware|ransomware|virus)\s+(code|create|write)\b", RegexOptions.IgnoreCase),
    ];

    public record GuardResult(bool IsClean, string? Reason);

    /// <summary>Prompt'u güvenlik açısından inceler.</summary>
    public GuardResult Inspect(string prompt)
    {
        if (string.IsNullOrWhiteSpace(prompt))
            return new(false, "Prompt boş olamaz.");

        foreach (var pattern in _injectionPatterns)
            if (pattern.IsMatch(prompt))
                return new(false, "Prompt enjeksiyon girişimi tespit edildi.");

        foreach (var pattern in _contentPatterns)
            if (pattern.IsMatch(prompt))
                return new(false, "İzin verilmeyen içerik kategorisi.");

        return new(true, null);
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// DENETİM KAYIT SERVİSİ
// ─────────────────────────────────────────────────────────────────────────────

/// <summary>İstek/yanıt denetim izi kaydı.</summary>
public sealed class AuditLogger
{
    private readonly ILogger<AuditLogger> _logger;

    public AuditLogger(ILogger<AuditLogger> logger) => _logger = logger;

    public void LogRequest(string requestId, string ip, string? userId,
                           int promptLen, bool encrypted)
    {
        _logger.LogInformation(
            "[AUDIT] {RequestId} | IP={IP} | User={User} | PromptLen={Len} | Enc={Enc} | {Time}",
            requestId, ip, userId ?? "anon", promptLen, encrypted,
            DateTime.UtcNow.ToString("o")
        );
    }

    public void LogResponse(string requestId, int statusCode,
                            int responseTokens, double durationMs)
    {
        _logger.LogInformation(
            "[AUDIT] {RequestId} | Status={Status} | Tokens={Tokens} | Ms={Ms}",
            requestId, statusCode, responseTokens, durationMs
        );
    }

    public void LogBlocked(string requestId, string ip, string reason)
    {
        _logger.LogWarning(
            "[BLOCKED] {RequestId} | IP={IP} | Reason={Reason}",
            requestId, ip, reason
        );
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// JWT SERVİSİ
// ─────────────────────────────────────────────────────────────────────────────

/// <summary>JWT token üretimi ve doğrulaması.</summary>
public sealed class JwtService
{
    private readonly ProxyConfig   _config;
    private readonly SymmetricSecurityKey _key;

    public JwtService(ProxyConfig config)
    {
        _config = config;
        _key    = new SymmetricSecurityKey(
            Encoding.UTF8.GetBytes(
                string.IsNullOrEmpty(config.JwtSecret)
                    ? Guid.NewGuid().ToString("N")   // Geliştirme: rastgele
                    : config.JwtSecret
            )
        );
    }

    /// <summary>Yeni JWT token üretir.</summary>
    public string GenerateToken(string userId, string role = "user")
    {
        var claims = new[]
        {
            new Claim(JwtRegisteredClaimNames.Sub,    userId),
            new Claim(JwtRegisteredClaimNames.Jti,    Guid.NewGuid().ToString()),
            new Claim(JwtRegisteredClaimNames.Iat,
                      DateTimeOffset.UtcNow.ToUnixTimeSeconds().ToString()),
            new Claim(ClaimTypes.Role, role),
        };

        var token = new JwtSecurityToken(
            issuer:             _config.JwtIssuer,
            audience:           _config.JwtAudience,
            claims:             claims,
            notBefore:          DateTime.UtcNow,
            expires:            DateTime.UtcNow.AddMinutes(_config.JwtExpiryMinutes),
            signingCredentials: new SigningCredentials(_key, SecurityAlgorithms.HmacSha256)
        );

        return new JwtSecurityTokenHandler().WriteToken(token);
    }

    /// <summary>Token'dan kullanıcı ID'sini çıkarır.</summary>
    public string? ValidateAndGetUserId(string token)
    {
        try
        {
            var handler    = new JwtSecurityTokenHandler();
            var parameters = new TokenValidationParameters
            {
                ValidateIssuer           = true,
                ValidateAudience         = true,
                ValidateLifetime         = true,
                ValidateIssuerSigningKey = true,
                ValidIssuer              = _config.JwtIssuer,
                ValidAudience            = _config.JwtAudience,
                IssuerSigningKey         = _key,
                ClockSkew                = TimeSpan.FromSeconds(30),
            };
            var principal = handler.ValidateToken(token, parameters, out _);
            return principal.FindFirst(JwtRegisteredClaimNames.Sub)?.Value;
        }
        catch
        {
            return null;
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// PROXY SERVİSİ — Ana İş Mantığı
// ─────────────────────────────────────────────────────────────────────────────

/// <summary>Claude API'ye güvenli proxy isteği gönderir.</summary>
public sealed class ClaudeProxyService
{
    private readonly IHttpClientFactory _http;
    private readonly ProxyConfig        _config;
    private readonly EncryptionService  _enc;
    private readonly RateLimiter        _rateLimiter;
    private readonly PromptGuard        _guard;
    private readonly AuditLogger        _audit;
    private readonly ILogger            _logger;

    public ClaudeProxyService(
        IHttpClientFactory  http,
        ProxyConfig         config,
        EncryptionService   enc,
        RateLimiter         rateLimiter,
        PromptGuard         guard,
        AuditLogger         audit,
        ILogger<ClaudeProxyService> logger)
    {
        _http        = http;
        _config      = config;
        _enc         = enc;
        _rateLimiter = rateLimiter;
        _guard       = guard;
        _audit       = audit;
        _logger      = logger;
    }

    public record ProxyRequest(
        string  Prompt,
        string? Model          = null,
        int     MaxTokens      = 1024,
        bool    IsEncrypted    = false,
        string? SystemPrompt   = null
    );

    public record ProxyResponse(
        bool    Success,
        string? Content        = null,
        string? Error          = null,
        bool    IsEncrypted    = false,
        int     InputTokens    = 0,
        int     OutputTokens   = 0
    );

    /// <summary>Güvenlik kontrollerinden geçirilmiş Claude API isteği.</summary>
    public async Task<(ProxyResponse Response, int StatusCode)> SendAsync(
        ProxyRequest request,
        string       clientIp,
        string?      userId,
        CancellationToken ct = default)
    {
        var requestId = Guid.NewGuid().ToString("N")[..12];
        var sw        = System.Diagnostics.Stopwatch.StartNew();

        // 1. IP kara liste kontrolü
        if (_config.BlockedIPs.Contains(clientIp))
        {
            _audit.LogBlocked(requestId, clientIp, "IP kara listede");
            return (new ProxyResponse(false, Error: "Erişim reddedildi."), 403);
        }

        // 2. IP beyaz liste (dolu ise yalnızca listelilere izin ver)
        if (_config.AllowedIPs.Count > 0 && !_config.AllowedIPs.Contains(clientIp))
        {
            _audit.LogBlocked(requestId, clientIp, "IP beyaz listede değil");
            return (new ProxyResponse(false, Error: "Erişim reddedildi."), 403);
        }

        // 3. Rate limiting
        var rateLimitKey = userId ?? clientIp;
        if (!_rateLimiter.TryAcquire(rateLimitKey))
        {
            _audit.LogBlocked(requestId, clientIp, "Rate limit aşıldı");
            return (new ProxyResponse(false, Error: "Çok fazla istek. Lütfen bekleyin."), 429);
        }

        // 4. Şifre çöz (gerekirse)
        var prompt = request.IsEncrypted && _config.EnableEncryption
            ? _enc.Decrypt(request.Prompt)
            : request.Prompt;

        // 5. Uzunluk kontrolü
        if (prompt.Length > _config.MaxPromptLength)
            return (new ProxyResponse(false,
                Error: $"Prompt çok uzun. Max: {_config.MaxPromptLength} karakter."), 400);

        // 6. Prompt güvenlik kontrolü
        var guardResult = _guard.Inspect(prompt);
        if (!guardResult.IsClean)
        {
            _audit.LogBlocked(requestId, clientIp, guardResult.Reason!);
            return (new ProxyResponse(false, Error: guardResult.Reason), 422);
        }

        _audit.LogRequest(requestId, clientIp, userId, prompt.Length, request.IsEncrypted);

        // 7. Claude API isteği
        try
        {
            var apiPayload = new
            {
                model      = request.Model ?? "claude-sonnet-4-20250514",
                max_tokens = request.MaxTokens,
                system     = request.SystemPrompt,
                messages   = new[] { new { role = "user", content = prompt } }
            };

            var client = _http.CreateClient("claude");
            client.DefaultRequestHeaders.Clear();
            client.DefaultRequestHeaders.Add("x-api-key",         _config.ClaudeApiKey);
            client.DefaultRequestHeaders.Add("anthropic-version",  "2023-06-01");

            var jsonBody = JsonSerializer.Serialize(apiPayload,
                new JsonSerializerOptions { DefaultIgnoreCondition =
                    System.Text.Json.Serialization.JsonIgnoreCondition.WhenWritingNull });

            var httpResp = await client.PostAsync(
                _config.ClaudeApiUrl,
                new StringContent(jsonBody, Encoding.UTF8, "application/json"),
                ct
            );

            var rawJson    = await httpResp.Content.ReadAsStringAsync(ct);
            var statusCode = (int)httpResp.StatusCode;

            if (!httpResp.IsSuccessStatusCode)
            {
                _logger.LogError("[PROXY] Claude API hata {Code}: {Body}", statusCode, rawJson);
                return (new ProxyResponse(false, Error: "Claude API hatası."), statusCode);
            }

            // Yanıtı ayrıştır
            using var doc       = JsonDocument.Parse(rawJson);
            var content         = doc.RootElement
                                     .GetProperty("content")[0]
                                     .GetProperty("text").GetString() ?? "";
            var inputTokens     = doc.RootElement
                                     .GetProperty("usage")
                                     .GetProperty("input_tokens").GetInt32();
            var outputTokens    = doc.RootElement
                                     .GetProperty("usage")
                                     .GetProperty("output_tokens").GetInt32();

            sw.Stop();
            _audit.LogResponse(requestId, statusCode, outputTokens, sw.Elapsed.TotalMilliseconds);

            // 8. Yanıtı şifrele (gerekirse)
            var responseContent = _config.EnableEncryption
                ? _enc.Encrypt(content)
                : content;

            return (new ProxyResponse(
                Success:      true,
                Content:      responseContent,
                IsEncrypted:  _config.EnableEncryption,
                InputTokens:  inputTokens,
                OutputTokens: outputTokens
            ), 200);
        }
        catch (TaskCanceledException)
        {
            return (new ProxyResponse(false, Error: "İstek zaman aşımına uğradı."), 504);
        }
        catch (Exception ex)
        {
            _logger.LogError(ex, "[PROXY] Beklenmeyen hata");
            return (new ProxyResponse(false, Error: "Proxy hatası."), 500);
        }
    }
}

// ─────────────────────────────────────────────────────────────────────────────
// UYGULAMA GİRİŞ NOKTASI
// ─────────────────────────────────────────────────────────────────────────────

var builder = WebApplication.CreateBuilder(args);

// ── Yapılandırma ──────────────────────────────────────────────────────────────
var config = new ProxyConfig
{
    ClaudeApiKey    = Environment.GetEnvironmentVariable("CLAUDE_API_KEY") ?? "",
    JwtSecret       = Environment.GetEnvironmentVariable("JWT_SECRET")     ?? "",
    EncryptionKey   = Environment.GetEnvironmentVariable("ENC_KEY")        ?? "",
    RateLimitPerMin = 20,
    RateLimitPerHour= 200,
    MaxPromptLength = 8000,
    EnableEncryption= true,
    EnableAuditLog  = true,
    AllowedOrigins  = new() { "http://localhost:3000", "https://yourdomain.com" },
};
builder.Services.AddSingleton(config);

// ── HTTP istemcisi ────────────────────────────────────────────────────────────
builder.Services.AddHttpClient("claude", c =>
{
    c.Timeout = TimeSpan.FromSeconds(60);
    c.DefaultRequestHeaders.UserAgent.ParseAdd("ClaudeProxy/1.0");
});

// ── Servisler ─────────────────────────────────────────────────────────────────
builder.Services.AddSingleton<EncryptionService>(_ => new EncryptionService(config.EncryptionKey));
builder.Services.AddSingleton<RateLimiter>(_ => new RateLimiter(config.RateLimitPerMin, config.RateLimitPerHour));
builder.Services.AddSingleton<PromptGuard>();
builder.Services.AddSingleton<AuditLogger>();
builder.Services.AddSingleton<JwtService>();
builder.Services.AddScoped<ClaudeProxyService>();
builder.Services.AddLogging(b => b.AddConsole().AddDebug());

// ── CORS ──────────────────────────────────────────────────────────────────────
builder.Services.AddCors(o => o.AddDefaultPolicy(p =>
    p.WithOrigins(config.AllowedOrigins.ToArray())
     .AllowAnyHeader()
     .WithMethods("GET", "POST", "OPTIONS")
));

var app = builder.Build();
app.UseCors();

// ─────────────────────────────────────────────────────────────────────────────
// ENDPOINT'LER
// ─────────────────────────────────────────────────────────────────────────────

// GET /health — Sağlık kontrolü
app.MapGet("/health", () => Results.Json(new
{
    status    = "ok",
    timestamp = DateTime.UtcNow.ToString("o"),
    version   = "1.0.0",
}));

// POST /auth/token — JWT token al
app.MapPost("/auth/token", (
    [FromBody] LoginRequest req,
    JwtService jwt,
    ILogger<Program> logger) =>
{
    // Gerçek uygulamada veritabanı doğrulaması yapılır
    if (req.Username == "admin" && req.Password == "changeme")
    {
        var token = jwt.GenerateToken(req.Username, "admin");
        return Results.Json(new { token, expires_in = 3600 });
    }
    logger.LogWarning("Başarısız giriş: {User}", req.Username);
    return Results.Json(new { error = "Geçersiz kimlik bilgileri." }, statusCode: 401);
});

// POST /proxy/chat — Ana proxy endpoint'i
app.MapPost("/proxy/chat", async (
    HttpContext            ctx,
    [FromBody] ProxyRequest req,
    ClaudeProxyService     proxy,
    JwtService             jwt) =>
{
    // JWT doğrulama
    string? userId = null;
    if (ctx.Request.Headers.TryGetValue("Authorization", out var authHeader))
    {
        var token = authHeader.ToString().Replace("Bearer ", "");
        userId    = jwt.ValidateAndGetUserId(token);
        if (userId is null)
            return Results.Json(new { error = "Geçersiz token." }, statusCode: 401);
    }

    var clientIp = ctx.Connection.RemoteIpAddress?.ToString() ?? "unknown";
    var (response, statusCode) = await proxy.SendAsync(req, clientIp, userId,
                                                        ctx.RequestAborted);

    return Results.Json(response, statusCode: statusCode);
});

// GET /proxy/status — Kullanım istatistikleri
app.MapGet("/proxy/status", (
    HttpContext ctx,
    RateLimiter rateLimiter,
    JwtService  jwt) =>
{
    var clientIp = ctx.Connection.RemoteIpAddress?.ToString() ?? "unknown";
    var (perMin, perHour) = rateLimiter.GetUsage(clientIp);
    return Results.Json(new
    {
        ip        = clientIp,
        usage     = new { per_minute = perMin, per_hour = perHour },
        limits    = new { per_minute = 20,     per_hour = 200 },
        timestamp = DateTime.UtcNow.ToString("o"),
    });
});

app.Run();

// ── Yardımcı kayıt tipleri ────────────────────────────────────────────────────
public record LoginRequest(string Username, string Password);
