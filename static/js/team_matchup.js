var game;

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
  
  $('.game-item').on('click', function() {
    $('.game-item').removeClass('active');
    $(this).addClass('active');
    game = $(this).data('game');
    loadBoard();
  });
  
  $('.slate .game-item:first').click();

  $('body').on('click','.team-stat table th',function() {
    var cls = $(this).closest('table').attr("class"),
        idx = $(this).index()+1;

    $('.team-stat th, .team-stat td').removeClass('active');
    var n_cls = `.team-stat .${cls} th:nth-child(${idx}), .team-stat .${cls} td:nth-child(${idx})`;
    $(n_cls).addClass('active');
  });
})

function loadBoard() {
  var data = { 
        min_afp: $('.afp').slider("values")[0],
        max_afp: $('.afp').slider("values")[1],
        game: game
      }

  $('.team-board').html('<div class="board-loading ml-1 mt-5">Loading ...</div>');

  $.post( "/team-match-up", data, function( data ) {
    $('.team-board').html(data);
  });
}
