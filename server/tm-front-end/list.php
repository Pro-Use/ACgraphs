<!DOCTYPE html>
<head>
    <link rel=stylesheet type=text/css href="../static/css/style-1.0.css">
</head>

<body class="list-body">

	<ul class="list-container">
		<?php 
			$x = 1; 
			while($x <= 100) {
		?>
			<li class="list-item row-max up">
				<span class="align-centre score col-xs-1">0.50721</span>
				<span class="align-centre icon"><span class="list-item-up-icon"> </span></span>
				<span class="align-centre source">REUTERS</span>
				<span class="list-item-content">Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam semper nisi non scelerisque ultrices.</span>
				<span class="align-centre time">16:35 GMT</span>
			</li>
			<li class="list-item row-max down">
				<span class="align-centre score col-xs-1">0.743303</span>
				<span class="align-centre icon"><span class="list-item-down-icon"> </span></span>
				<span class="align-centre source">FT</span>
				<span class="list-item-content">Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam semper nisi non scelerisque ultrices.</span>
				<span class="align-centre time">16:33 GMT</span>
			</li>
			<li class="list-item row-max down">
				<span class="align-centre score col-xs-1">0.50721</span>
				<span class="align-centre icon"><span class="list-item-down-icon"> </span></span>
				<span class="align-centre source">DOW JONES</span>
				<span class="list-item-content">Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam semper nisi non scelerisque ultrices.</span>
				<span class="align-centre time">16:34 GMT</span>
			</li>
			<?php $x++;} ?>
	</ul>
	


<!-- {%for i in range(0, tickers)%}
    <div class="TickerNews">
    	<div class="ticker-news-inner">
	    	<h2 class="ticker-title">Breaking News</h2>
	        <div class="ti_wrapper" style="left:{{position}}px">
	            <div id="ti_content-{{i}}">
	                {{html}}
	            </div>
	        </div>
	    </div>
    </div>
{%endfor%} -->

</body>
