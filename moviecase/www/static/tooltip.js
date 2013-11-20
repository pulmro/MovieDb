
// Remember to add <div class="tip"></div> to your html page
$(document).ready(function() {
	
	$(".btn").hover(function(){
        tip = $('.tip');
        tip.text($(this).attr('tip'));
        y = $(this).offset().top+$(this).height()+5;
        x = $(this).offset().left;
        tip.css({top:y, left:x});
        tip.show(); //Show tooltip
    	}, function() {
        tip.hide(); //Hide tooltip
    	});

});
