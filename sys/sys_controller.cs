using System;
using System.Collections.Generic;
using System.Diagnostics;
using System.Threading.Tasks;
using Microsoft.AspNetCore.Mvc;
using Microsoft.Extensions.Logging;

namespace Sys
{
    /// <summary>
    /// <b>SysController</b> — Sistem bilgilerini sunan ASP.NET Core MVC denetleyicisi.
    /// <para>
    /// Rota: <c>/sys</c><br/>
    /// GET  /sys          → Index()<br/>
    /// GET  /sys/durum    → Durum()<br/>
    /// GET  /sys/versiyon → Versiyon()<br/>
    /// GET  /sys/hata     → Error()
    /// </para>
    /// </summary>
    /// <remarks>
    /// Düzeltmeler (orijinal sys_controller.cs):
    /// <list type="bullet">
    ///   <item>Sınıf adı PascalCase'e uygun hale getirildi: sys_controller → SysController</item>
    ///   <item>Namespace düzeltildi: sys → Sys</item>
    ///   <item>Gereksiz using direktifleri temizlendi</item>
    ///   <item>Yeni endpoint'ler ve XML dökümantasyonu eklendi</item>
    /// </list>
    /// </remarks>
    [ApiController]
    [Route("[controller]")]
    public class SysController : Controller
    {
        private readonly ILogger<SysController> _logger;

        /// <summary>
        /// SysController yapıcısı.
        /// </summary>
        /// <param name="logger">ASP.NET Core DI tarafından enjekte edilen logger.</param>
        public SysController(ILogger<SysController> logger)
        {
            _logger = logger ?? throw new ArgumentNullException(nameof(logger));
        }

        // ── GET /sys ─────────────────────────────────────────────────────────

        /// <summary>
        /// Sistem ana görünümünü döndürür.
        /// </summary>
        /// <returns>Index.cshtml görünümü.</returns>
        [HttpGet]
        public IActionResult Index()
        {
            _logger.LogInformation("SysController.Index çağrıldı.");
            return View();
        }

        // ── GET /sys/durum ────────────────────────────────────────────────────

        /// <summary>
        /// Sistemin anlık çalışma durumunu JSON olarak döndürür.
        /// </summary>
        /// <returns>
        /// <see cref="OkObjectResult"/> içinde:
        /// <list type="bullet">
        ///   <item><c>durum</c>: "çalışıyor"</item>
        ///   <item><c>zaman</c>: ISO 8601 zaman damgası</item>
        ///   <item><c>makine</c>: sunucu adı</item>
        /// </list>
        /// </returns>
        [HttpGet("durum")]
        public IActionResult Durum()
        {
            var sonuc = new
            {
                durum   = "çalışıyor",
                zaman   = DateTime.UtcNow.ToString("o"),
                makine  = Environment.MachineName,
                pid     = Environment.ProcessId,
            };
            _logger.LogInformation("Durum sorgulandı: {Zaman}", sonuc.zaman);
            return Ok(sonuc);
        }

        // ── GET /sys/versiyon ─────────────────────────────────────────────────

        /// <summary>
        /// Uygulama ve çevre versiyonu bilgilerini döndürür.
        /// </summary>
        /// <returns>Versiyon bilgisi JSON nesnesi.</returns>
        [HttpGet("versiyon")]
        public IActionResult Versiyon()
        {
            return Ok(new
            {
                uygulama = "1.0.0",
                dotnet   = Environment.Version.ToString(),
                os       = Environment.OSVersion.VersionString,
            });
        }

        // ── GET /sys/hata ─────────────────────────────────────────────────────

        /// <summary>
        /// Hata görünümünü döndürür. Önbelleğe alınmaz.
        /// </summary>
        /// <returns>Error.cshtml görünümü.</returns>
        [HttpGet("hata")]
        [ResponseCache(Duration = 0, Location = ResponseCacheLocation.None, NoStore = true)]
        public IActionResult Error()
        {
            _logger.LogWarning("Hata sayfası istendi. RequestId={RequestId}",
                Activity.Current?.Id ?? HttpContext.TraceIdentifier);
            return View("Error");
        }
    }
}