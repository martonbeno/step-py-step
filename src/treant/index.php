<?php
function normalize($s){
	$ret = $s;
	$ret = preg_replace('/\r/', '', $ret);
	$ret = preg_replace('/\n/', '\\n', $ret);
	$ret = preg_replace('/\t/', '\\t', $ret);
	return $ret;
}

function text_to_color($text, $color){
	$needsBackground = $color !== null;

	if($needsBackground){
		$ret = '<span style=';
		$ret .='"background-color:'.$color;
		$ret .= '">';
		$ret .= $text;
		$ret .= '</span>';
		return $ret;
	}
	return $text;
}

//TODO nem-ascii karakterekre még mindig nem jó
function color_part_of_text($text, $from_index, $to_index, $color){
	$ret = mb_substr($text, 0, 0+$from_index, 'utf-8');
	$ret .= text_to_color(mb_substr($text, $from_index, $to_index-$from_index+1, 'utf-8'), $color);
	$ret .= mb_substr($text, $to_index+1, mb_strlen($text, 'utf-8'), 'utf-8');
	return $ret;
}

function node_to_colored_code($node){
	$code = $node['code'];
	$lines = preg_split('/\r\n|\r|\n/', $code);
	$ret = "";
	
	
	$act_line = 0;
	$unended_section = false;
	foreach($lines as $line){
		if($act_line == $node['highlight']['from_line'] && $act_line == $node['highlight']['to_line']){
			$ret .= color_part_of_text($line, $node['highlight']['from_char'], $node['highlight']['to_char'], "yellow");
			$unended_section = false;
		}
		else if($act_line == $node['highlight']['from_line']){
			$ret .= color_part_of_text($line, $node['highlight']['from_char'], mb_strlen($line, 'utf-8'), "yellow");
			$unended_section = true;
		}
		else if($act_line == $node['highlight']['from_line']){
			$ret .= color_part_of_text($line, 0, $node['highlight']['to_char'], "yellow");
			$unended_section = false;
		}
		else{
			$ret .= $line;
		}
		$ret .= PHP_EOL;
		$act_line ++;
	}
	
	
	// print_r($lines);
	return $ret;
}

$input_received = isset($_POST['code']);
$code = $input_received ? $_POST['code'] : '';

?>

<html>
    <head>
		<meta charset="utf-8">
		<meta http-equiv="X-UA-Compatible" content="IE=edge,chrome=1">
		<meta name="viewport" content="width=device-width">
		<title> Chart emulation </title>
		<link rel="stylesheet" href="./Treant.css">
		<link rel="stylesheet" href="./super-simple.css">
		<script src="https://ajax.googleapis.com/ajax/libs/jquery/3.5.1/jquery.min.js"></script>
	</head>
<body>
	<div>
		<textarea id="code" rows=10 cols=100></textarea><br>
		<script src="./allowtabs.js"></script>
		<button onclick="readcode()">submit</button>
		<button onclick="first_section()">beginning</button>
		<button onclick="next_section()">next</button>
		<button onclick="evaluate_part()">evaluate</button>
		<pre>
			<p id="analysis"></p>
		</pre>
			<p id="value"></p>
		<pre>
<?php
	
	$code = normalize($code);
	if($input_received){
		
		echo "------------<br>";
		
		$exec_command = "python C:\\Users\\HAL9000\\Desktop\\ik\\szakdoga\\src\\main.py ";
		// $exec_command .= $code;
		$exec_command .= '"' . addcslashes($code, '"') . '"';
		echo $exec_command . '<br>';
		$json_answer = exec($exec_command);
		$answer = json_decode($json_answer, true);
		$node_structure = json_encode($answer['treant']);
		$analysis = $answer['analysis'];
		
		
		$highlighted_analysis = array();
		foreach($analysis as $node){
			$highlighted_analysis[] = node_to_colored_code($node);
		}
		
		$evaluation_analysis = array();
		foreach($analysis as $node){
			$evaluation_analysis[] = $node['evaluation'];
		}
		
		$analysis_json = json_encode($highlighted_analysis);
		$evaluation_json = json_encode($evaluation_analysis);
	}
?>
		</pre>
		
	</div>
	<div class="chart" id="OrganiseChart-simple">
	</div>
	<script src="./raphael.js"></script>
	<script src="./Treant.js"></script>
	<script src="./fa.js"></script>
	
	<script>
		
		
		var act_section_index = 0;
		var act_section;
		
		function readcode(){
			ta = document.getElementById("code").value;
			console.log(ta);
			$.ajax({
			  type: "POST",
			  url: "./proba.py",
			  data: { param: "{'jo'}"}
			});
		}
		
		function first_section(){
			act_section_index = 0;
			next_section();
		}
		
		function next_section(){
			act_section = analysis[act_section_index];
			console.log(act_section);
			document.getElementById("analysis").innerHTML = analysis[act_section_index].toString();
			act_section_index ++;
		}
		
		function evaluate_part(){
			var value = evaluation[act_section_index-1]
			console.log("kiértékelem", evaluation);
			console.log("konkrét érték", act_section_index-1, value);
			
			value = value !== null ? value.toString() : '';
			document.getElementById("value").innerHTML = value;
			
		}
	</script>

</body>
</html>