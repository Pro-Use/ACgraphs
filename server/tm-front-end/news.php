<!DOCTYPE html>
<head>
    <link rel=stylesheet type=text/css href="../static/css/style-1.0.css">
</head>

<body class="news">

	<ul id="left-news-feed" class="news-list">
		<?php 
			$x = 1; 
			while($x <= 100) {
		?>
			<li class="news-list-item row-max red">
				<span class="align-centre emotion col-xs-1">Anger</span>
				<span class="align-centre span col-xs-1">0.50721</span>
				<span class=" news-headline col-xs-8">Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam semper nisi non scelerisque ultrices.</span>
				<span class="align-centre time col-xs-2">16:35 GMT</span>
			</li>
			<li class="news-list-item row-max green">
				<span class="align-centre emotion col-xs-1">Anger</span>
				<span class="align-centre span col-xs-1">0.50721</span>
				<span class=" news-headline col-xs-8">Lorem ipsum dolor sit amet, consectetur adipiscing elit. Nullam semper nisi non scelerisque ultrices.</span>
				<span class="align-centre time col-xs-2">16:35 GMT</span>
			</li>
			<?php $x++;} ?>
	</ul>
	


	<div class="news-ticker-wrapper">
		<div class="news-ticker-wrapper-inner">
			<div class="news-ticker-title">
				BREAKING NEWS
			</div>
			<div class="news-ticker-container">
				<!-- NEWS TICKER SCROLLING CONTENT GOES HERE -->
				<div class="news-ticker-item">
					<span class="ticker-up-icon"> </span><span class="news-ticker-item-text">EXTREMELY NLIKELYT </span>
				</div>
				<div class="news-ticker-item">
					<span class="ticker-down-icon"> </span><span class="news-ticker-item-text">LOREM IPSUM DOLAR</span>
				</div>
				<!-- END SCROLLING CONTENT -->
			</div>
		</div>
	</div>


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
