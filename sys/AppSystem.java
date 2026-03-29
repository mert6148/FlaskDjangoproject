import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.UUID;

/**
 * <b>System</b> — Sistem kodu üretici sınıf.
 *
 * <p>Bu sınıf zaman damgası ve UUID parçasını birleştirerek
 * tekil sistem kodları üretir.</p>
 *
 * <pre>
 * Örnek çıktı: SYS-20251029143022-a3f9c1d8
 * </pre>
 *
 * <h3>Kullanım</h3>
 * <pre>{@code
 * String kod = System.generateSystemCode();
 * System.out.println(kod);  // SYS-20251029143022-a3f9c1d8
 * }</pre>
 *
 * <h3>Düzeltmeler (orijinal system.java)</h3>
 * <ul>
 *   <li>Sınıf adı {@code java.lang.System} ile çakışıyor — {@code AppSystem} olarak yeniden adlandırıldı</li>
 *   <li>Javadoc ve parametre açıklamaları eklendi</li>
 *   <li>Kod biçimlendirmesi PascalCase/camelCase kurallarına uygun hale getirildi</li>
 *   <li>{@code generateSystemCode()} dönüş değeri için doğrulama eklendi</li>
 * </ul>
 *
 * @author  Mert Doğanay
 * @version 1.0.0
 * @since   2025-01-01
 */
public class AppSystem {

    /** Sistem kodu öneki. */
    private static final String ONEK = "SYS";

    /** Zaman damgası biçimi. */
    private static final DateTimeFormatter BICIMLENDIRICI =
            DateTimeFormatter.ofPattern("yyyyMMddHHmmss");

    /** UUID parçası uzunluğu. */
    private static final int UUID_UZUNLUK = 8;

    // ── Ana giriş noktası ─────────────────────────────────────────────────────

    /**
     * Uygulamanın giriş noktası.
     *
     * @param args Komut satırı argümanları (kullanılmıyor).
     */
    public static void main(String[] args) {
        String kod = generateSystemCode();
        java.lang.System.out.println("Üretilen Kod: " + kod);

        // Çoklu kod üretimi örneği
        java.lang.System.out.println("\nÖrnek Kodlar:");
        for (int i = 1; i <= 3; i++) {
            java.lang.System.out.printf("  %d. %s%n", i, generateSystemCode());
        }
    }

    // ── Kod üretici ───────────────────────────────────────────────────────────

    /**
     * Tekil bir sistem kodu üretir.
     *
     * <p>Kod biçimi: {@code SYS-<zaman>-<uuid>}</p>
     * <ul>
     *   <li>{@code zaman}  — {@code yyyyMMddHHmmss} biçiminde yerel zaman</li>
     *   <li>{@code uuid}   — rastgele UUID'nin ilk {@value #UUID_UZUNLUK} karakteri</li>
     * </ul>
     *
     * @return Tekil sistem kodu, örn. {@code SYS-20251029143022-a3f9c1d8}
     */
    public static String generateSystemCode() {
        String zaman    = LocalDateTime.now().format(BICIMLENDIRICI);
        String uuidPart = UUID.randomUUID().toString().substring(0, UUID_UZUNLUK);
        return ONEK + "-" + zaman + "-" + uuidPart;
    }

    // ── Doğrulama ─────────────────────────────────────────────────────────────

    /**
     * Verilen kod dizisinin geçerli sistem kodu biçimine sahip olup
     * olmadığını kontrol eder.
     *
     * @param kod Doğrulanacak kod dizisi.
     * @return {@code true} geçerli biçimdeyse, {@code false} aksi hâlde.
     * @throws IllegalArgumentException {@code kod} null ise.
     */
    public static boolean gecerliMi(String kod) {
        if (kod == null) throw new IllegalArgumentException("Kod null olamaz.");
        return kod.matches("^SYS-\\d{14}-[a-f0-9]{8}$");
    }
}