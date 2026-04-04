using System;
using System.Collections.Generic;
using System.IO;
using System.Linq;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;

namespace app.src
{
    /// <summary>
    /// API dizinlerini ve dosyalarını kontrol etmek için otomatik controller
    /// </summary>
    [ApiController]
    [Route("api/[controller]")]
    public class ApiController : ControllerBase
    {
        private readonly string _basePath;
        private readonly ILogger<ApiController> _logger;

        public ApiController(ILogger<ApiController> logger)
        {
            _logger = logger;
            _basePath = AppContext.BaseDirectory;
        }

        /// <summary>
        /// Tüm API dizinlerini tarar ve yapısını döndürür
        /// GET: api/controller/scan
        /// </summary>
        [HttpGet("scan")]
        public async Task<IActionResult> ScanApiDirectories()
        {
            try
            {
                var apiDirs = new List<DirectoryStructure>();
                var apiPath = Path.Combine(_basePath, "api");

                if (!Directory.Exists(apiPath))
                {
                    return NotFound(new { message = "API dizini bulunamadı" });
                }

                apiDirs.AddRange(GetDirectoryStructure(apiPath));

                return Ok(new
                {
                    success = true,
                    timestamp = DateTime.UtcNow,
                    directories = apiDirs
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "API dizinleri taraması sırasında hata oluştu");
                return StatusCode(500, new { error = ex.Message });
            }
        }

        /// <summary>
        /// Belirtilen dizinin dosyalarını listeler
        /// GET: api/controller/list-files
        /// </summary>
        [HttpGet("list-files")]
        public async Task<IActionResult> ListFiles([FromQuery] string path = "")
        {
            try
            {
                var fullPath = string.IsNullOrEmpty(path)
                    ? Path.Combine(_basePath, "api")
                    : Path.Combine(_basePath, "api", path);

                if (!Directory.Exists(fullPath))
                {
                    return NotFound(new { message = "Dizin bulunamadı" });
                }

                var files = Directory.GetFiles(fullPath)
                    .Select(f => new
                    {
                        name = Path.GetFileName(f),
                        extension = Path.GetExtension(f),
                        size = new FileInfo(f).Length,
                        modified = File.GetLastWriteTime(f)
                    })
                    .ToList();

                var subdirs = Directory.GetDirectories(fullPath)
                    .Select(d => Path.GetFileName(d))
                    .ToList();

                return Ok(new
                {
                    success = true,
                    path = path,
                    files = files,
                    subdirectories = subdirs,
                    fileCount = files.Count,
                    directoryCount = subdirs.Count
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Dosya listesi alınırken hata oluştu");
                return StatusCode(500, new { error = ex.Message });
            }
        }

        /// <summary>
        /// API dizinlerinin istatistiklerini döndürür
        /// GET: api/controller/statistics
        /// </summary>
        [HttpGet("statistics")]
        public async Task<IActionResult> GetStatistics()
        {
            try
            {
                var apiPath = Path.Combine(_basePath, "api");

                if (!Directory.Exists(apiPath))
                {
                    return NotFound(new { message = "API dizini bulunamadı" });
                }

                var stats = GetDirectoryStatistics(apiPath);

                return Ok(new
                {
                    success = true,
                    statistics = stats
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "İstatistik alınırken hata oluştu");
                return StatusCode(500, new { error = ex.Message });
            }
        }

        /// <summary>
        /// Dizin yapısını kontrol eder ve danışmanlık sağlar
        /// GET: api/controller/validate
        /// </summary>
        [HttpGet("validate")]
        public async Task<IActionResult> ValidateDirectoryStructure()
        {
            try
            {
                var validationResults = new List<ValidationResult>();
                var apiPath = Path.Combine(_basePath, "api");

                if (!Directory.Exists(apiPath))
                {
                    validationResults.Add(new ValidationResult
                    {
                        level = "Warning",
                        message = "API dizini bulunamadı",
                        suggestion = "API dizinini oluşturun"
                    });
                }
                else
                {
                    // Boş dizin kontrolü
                    if (!Directory.GetFiles(apiPath, "*.*", SearchOption.AllDirectories).Any())
                    {
                        validationResults.Add(new ValidationResult
                        {
                            level = "Warning",
                            message = "API dizini boş",
                            suggestion = "API dosyalarını ekleyin"
                        });
                    }

                    // Dosya türü kontrolü
                    var fileCounts = GetFileTypeStatistics(apiPath);
                    validationResults.Add(new ValidationResult
                    {
                        level = "Info",
                        message = $"Dosya türü dağılımı: {string.Join(", ", fileCounts)}",
                        suggestion = ""
                    });
                }

                return Ok(new
                {
                    success = true,
                    validationResults = validationResults
                });
            }
            catch (Exception ex)
            {
                _logger.LogError(ex, "Doğrulama sırasında hata oluştu");
                return StatusCode(500, new { error = ex.Message });
            }
        }

        // ============= YARDIMCI FONKSİYONLAR =============

        private List<DirectoryStructure> GetDirectoryStructure(string path, int maxDepth = 3, int currentDepth = 0)
        {
            var result = new List<DirectoryStructure>();

            if (currentDepth >= maxDepth)
                return result;

            try
            {
                var directories = Directory.GetDirectories(path);
                foreach (var dir in directories)
                {
                    var dirName = Path.GetFileName(dir);
                    var fileCount = Directory.GetFiles(dir).Length;

                    result.Add(new DirectoryStructure
                    {
                        name = dirName,
                        fileCount = fileCount,
                        subdirectories = GetDirectoryStructure(dir, maxDepth, currentDepth + 1)
                    });
                }
            }
            catch (UnauthorizedAccessException ex)
            {
                _logger.LogWarning(ex, $"Erişim reddedildi: {path}");
            }

            return result;
        }

        private dynamic GetDirectoryStatistics(string path)
        {
            var totalFiles = 0;
            var totalDirectories = 0;
            var totalSize = 0L;

            try
            {
                var dirs = Directory.GetDirectories(path, "*", SearchOption.AllDirectories);
                totalDirectories = dirs.Length;

                var files = Directory.GetFiles(path, "*", SearchOption.AllDirectories);
                totalFiles = files.Length;
                totalSize = files.Sum(f => new FileInfo(f).Length);
            }
            catch (UnauthorizedAccessException ex)
            {
                _logger.LogWarning(ex, "Dizin istatistikleri alınırken erişim sorunları");
            }

            return new
            {
                totalFiles = totalFiles,
                totalDirectories = totalDirectories,
                totalSizeBytes = totalSize,
                totalSizeMB = Math.Round(totalSize / (1024.0 * 1024.0), 2)
            };
        }

        private List<string> GetFileTypeStatistics(string path)
        {
            try
            {
                var files = Directory.GetFiles(path, "*.*", SearchOption.AllDirectories);
                var fileTypes = files
                    .GroupBy(f => Path.GetExtension(f))
                    .Select(g => $"{g.Key}: {g.Count()}")
                    .ToList();

                return fileTypes.Any() ? fileTypes : new List<string> { "Dosya türü bulunamadı" };
            }
            catch
            {
                return new List<string> { "Dosya türü analizi hatası" };
            }
        }
    }

    // ============= MODEL KLASLARı =============

    public class DirectoryStructure
    {
        public string name { get; set; }
        public int fileCount { get; set; }
        public List<DirectoryStructure> subdirectories { get; set; } = new();
    }

    public class ValidationResult
    {
        public string level { get; set; }
        public string message { get; set; }
        public string suggestion { get; set; }
    }
}