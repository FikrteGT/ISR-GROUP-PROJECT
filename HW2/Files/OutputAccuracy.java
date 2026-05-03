import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.Arrays;
import java.util.Map;
import java.util.stream.Collectors;

public class OutputAccuracy {

    private static int totalLowErrorLines = 0;
    private static int totalNormalizedValues = 0;

    public static void main(String[] args) throws IOException {

        // ✅ SAFE RELATIVE PATHS (WORKS IN ANY MACHINE IF FILES ARE IN PROJECT FOLDER)
        Path baseDir = Paths.get(System.getProperty("user.dir"));

        Path expected = baseDir.resolve("Stemmed/out_stemmed.txt");
        Path actual = baseDir.resolve("Stemmed/OkapiBM25_Results_File.txt");

        // Check if files exist before running
        if (!Files.exists(expected)) {
            System.out.println("ERROR: Missing file -> " + expected);
            return;
        }

        if (!Files.exists(actual)) {
            System.out.println("ERROR: Missing file -> " + actual);
            return;
        }

        compareFiles(expected, actual);
    }

    public static void compareFiles(Path expected, Path actual) throws IOException {

        Map<String, String[]> expectedMap = fileToMap(expected);
        Map<String, String[]> actualMap = fileToMap(actual);

        int errors =
                expectedMap.entrySet()
                        .stream()
                        .map(entry ->
                                compare(
                                        entry.getKey(),
                                        entry.getValue(),
                                        actualMap.get(entry.getKey())
                                )
                        )
                        .filter(b -> b)
                        .mapToInt(b -> 1)
                        .sum();

        System.out.println("\n================ RESULT ================");
        System.out.println("Total terms: " + expectedMap.size());
        System.out.println("Errors (>5%): " + errors);
        System.out.println("Small errors ignored (<5%): " + totalLowErrorLines);
        System.out.println("Normalized differences (±1 allowed): " + totalNormalizedValues);
        System.out.println("========================================");
    }

    private static boolean compare(String term, String[] expectedValues, String[] actualValues) {

        if (actualValues == null) {
            System.out.println("Missing term in output: " + term);
            return true;
        }

        int expectedDF = Integer.parseInt(expectedValues[0]);
        int expectedTTF = Integer.parseInt(expectedValues[1]);

        int actualDF = Integer.parseInt(actualValues[0]);
        int actualTTF = Integer.parseInt(actualValues[1]);

        boolean error = false;

        double dfError = errorPercent(expectedDF, actualDF);
        double ttfError = errorPercent(expectedTTF, actualTTF);

        if (dfError > 5.0) {
            error = true;
            System.out.printf("DF error %.2f%% for term %s (%d vs %d)%n",
                    dfError, term, expectedDF, actualDF);
        } else if (dfError > 0.0) {
            totalLowErrorLines++;
        }

        if (ttfError > 5.0) {
            error = true;
            System.out.printf("TTF error %.2f%% for term %s (%d vs %d)%n",
                    ttfError, term, expectedTTF, actualTTF);
        } else if (ttfError > 0.0) {
            totalLowErrorLines++;
        }

        return error;
    }

    private static double errorPercent(int expectedValue, int actualValue) {

        int diff = Math.abs(expectedValue - actualValue);

        if (diff == 0) return 0.0;

        // allow small tolerance
        if (diff <= 1 && expectedValue >= 5) {
            totalNormalizedValues++;
            return 0.0;
        }

        return Math.abs((expectedValue - actualValue) / (double) expectedValue * 100);
    }

    private static Map<String, String[]> fileToMap(Path filePath) throws IOException {

        return Files.lines(filePath)
                .map(line -> line.trim().split("\\s+"))
                .filter(arr -> arr.length >= 3) // safety check
                .collect(Collectors.toMap(
                        arr -> arr[0],
                        arr -> Arrays.copyOfRange(arr, 1, arr.length),
                        (oldValue, newValue) -> oldValue // ignore duplicates
                ));
    }
}