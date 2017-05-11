/**
 * Created by Martin Peedosk on 30.10.2016.
 */


import org.deeplearning4j.models.embeddings.loader.WordVectorSerializer;
import org.deeplearning4j.models.word2vec.Word2Vec;
import spark.ModelAndView;
import spark.template.thymeleaf.ThymeleafTemplateEngine;

import java.io.BufferedReader;
import java.io.File;
import java.io.IOException;
import java.io.InputStreamReader;
import java.net.URL;
import java.net.URLConnection;
import java.nio.charset.Charset;
import java.util.*;

import static spark.Spark.*;


public class Main {

    // Word2vec mudel mille põhjal leitakse sarnasus
    static Word2Vec model;
    private static final String trainingModel = "python/lemmas.cbow.s200.w2v.bin";

    static {
        File gModel = new File(trainingModel);
        model = WordVectorSerializer.readWord2VecModel(gModel);
    }

    // Olenevalt operatsioonisüsteemist kasutatakse pythoni väljakutsumiseks erinevat käsku
    private static final String python = getPythonType();

    public static void main(String[] args) {
        staticFiles.location("/public");

        // Teksti lihtsustamise päring
        post("/simplify", (request, response) -> {

            // Kasutaja sisestatud tekst
            String input = request.queryParams("input").replace("\"", "'");

            // Lävend
            String threshold =  request.queryParams("threshold");

            if(input.length() == 0){
                input = " ";
            }

            // Küsime lihtsustatud teksti Pythoni programmilt
            String result = getPythonOutput(input, request.host(), threshold);

            // Tagastame tulemuse
            return result.length() > 0 ? result : " " ;
        });

        // Põhilehe kuvamise päring
        get("/", (request, response) -> {
            Map<String, Object> model = new HashMap<>();
            return new ModelAndView(model, "site");
        }, new ThymeleafTemplateEngine());

        // Word2vec sarnasuse leidmise päring
        get("/similarity", (request, response) -> {
            String word1 = request.queryParams("word1");
            String word2 = request.queryParams("word2");

            return model.similarity(word1, word2);
        });
    }

    // Teksti edastamine Python programmile
    private static String getPythonOutput(String input, String host, String threshold) {
        StringBuilder output = new StringBuilder();
        try {
            ProcessBuilder pb = new ProcessBuilder(python, "python/simplify.py", input, host, threshold);
            pb.redirectErrorStream(true);

            Process proc = pb.start();

            String line;
            BufferedReader in = new BufferedReader(new InputStreamReader(
                    proc.getInputStream(), System.getProperty("sun.jnu.encoding")));
            while ((line = in.readLine()) != null) {
                output.append(line).append("\n");
            }
            proc.destroy();
        } catch (IOException e) {
            e.printStackTrace();
        }
        return output.toString();
    }

    // Tagastame pythoni väljakutsumise käsu
    private static String getPythonType() {
        String os = System.getProperty("os.name");
        if (os.startsWith("Windows"))
            return "python";
        return "python3";
    }
}