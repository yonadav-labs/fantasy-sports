$(document).ready(function () {
  $( ".slider-range" ).slider({
    range: true,
    min: 1,
    step: 0.5,
    max: 100,
    values: [ 1, 100 ],
    change: function( event, ui ) {
      $(this).parent().find('.slider-val').val(ui.values[ 0 ] + " - " + ui.values[ 1 ]);
      loadBoard();
    }
  });

  $( ".slider-val" ).val("1 - 100");

  $('.slate input').on('change', function() {
    loadBoard();
  });

  $('.position-filter .nav-item a').on('click', function() {
    $('.position-filter .nav-item a').removeClass('active');
    $(this).toggleClass('active');
    loadBoard();
  });

  loadBoard();
})

function loadBoard() {
  var games = '';
  $('.slate').find('input:checked').each(function() {
    games += $(this).val()+';';
  })

  var data = { 
        loc: $('.filters select.loc').val(), 
        ds: $('.filters select.ds').val(),
        pos: $('.position-filter .nav-item a.active').html(),
        min_afp: $('.afp').slider("values")[0],
        max_afp: $('.afp').slider("values")[1],
        min_sfp: $('.sfp').slider("values")[0],
        max_sfp: $('.sfp').slider("values")[1],
        games: games
      };

  $('.player-board').html('<div class="board-loading ml-1 mt-5">Loading ...</div>');
  $.post( "/player-match-up", data, function( data ) {
    $('.player-board').html(data);
  });
}
