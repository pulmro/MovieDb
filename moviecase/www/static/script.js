$(document).ready(function() {
	$('.movielist li:odd').css('background-color','#dadada');
	$('.movielist div.more').hide();
	$('.movielist ul div.actions').hide();
	$('.movielist li').hover(
		function() { $(this).children('div.headline').children('div.actions').show();},
		function() { $(this).children('div.headline').children('div.actions').hide(); }
	);
	$('.movielist li').click(
		function() {
			$(this).children('div.more').animate({opacity: 'toggle', height:'toggle'}, 'slow', 'swing');
			$('body,html').scroll();
		}
	);
	
	$('.movielist div.more').children('img').lazyload();
	
	$('#dialog').dialog({
		autoOpen: false,
		height: 200,
		width: 300,
		modal: true,
		resizable: false,
		buttons: {
			'Cerca': function() {
				alert('!!!');
			},
			Continue: function() {
				$(this).dialog('close');
			}
		}
	});
	jQuery.expr[":"].Contains = jQuery.expr.createPseudo(function(arg) {
		return function( elem ) {
			return jQuery(elem).text().toUpperCase().indexOf(arg.toUpperCase()) >= 0;
		};
	});
	$('#filter').keyup(
		function() {
			if ($(this).val()!="") {
				$('.movielist li').hide();
				query = 'div.title:Contains("'+$(this).val()+'")';
				$(query).parentsUntil('ul').show();
			}
			else {
				$('.movielist li').show();
			}
		}
	);
	/*$('#movielist div.edit').click(
		function() {
			$('#dialog').dialog('open');
		}
	);*/ 
}); 
