import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.UUID;

public class system {

    public static void main(String[] args) {
        String code = generateSystemCode();
        System.out.println("Üretilen Kod: " + code);
    }

    public static String generateSystemCode() {
        String time = LocalDateTime.now()
                .format(DateTimeFormatter.ofPattern("yyyyMMddHHmmss"));

        String uuidPart = UUID.randomUUID().toString().substring(0, 8);

        return "SYS-" + time + "-" + uuidPart;
    }
}