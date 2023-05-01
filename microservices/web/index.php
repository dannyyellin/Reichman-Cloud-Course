<html>
    <head>
        <title>My Words</title>
    </head>

    <body>
        <h1>Welcome to my words</h1>
        <ul>
            <?php
            $json = file_get_contents('http://word-service/words');
            // echo $json
             // $json is a JSON string of the form (for example): "{\"1\":\"happy\"}, {\"2\":\"plane\"}"
                $arr = explode(",",$json);  // $arr is an array of strings.
                foreach ($arr as $word) {
                    # need to remove all the extra formatting
                    $word = str_replace('{','',$word);
                    $word = str_replace('}','',$word);
                    $word = str_replace('\"','', $word);
                    $word = str_replace('"','', $word);
                    echo "<li>$word</li>";
                }
            ?>
        </ul>
    </body>
</html>
