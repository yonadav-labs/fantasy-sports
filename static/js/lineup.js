$(function() {
  $('.nav-tabs.ds a').on('shown.bs.tab', function(event) {
    getPlayers();
  });

  $('.slate input').on('change', function() {
    getPlayers();
  });

  $('.nav-tabs.ds .nav-link').click(function () {
    $('#div-result').html('');
    $('#ds').val($(this).text());
  });

  $('.nav-tabs.ds .nav-link:first').click();

  $('.btn-export').click(function() {
    var num_players = $('input[type="checkbox"]:checked').length;
    if (num_players == 0) {
      alert('Please choose players.');
      return false;
    }

    $('#dlg-export').modal();
  });

  $('.btn-calc').click(function() {
    var num_players = $('input[type="checkbox"]:checked').length;
    if (num_players < 8) {
      alert('Please choose more than 8 players.');
      return
    }

    $('#div-result').html('<div class="font-weight-bold ml-5 pl-4" style="margin-top: 48vh;">Calculating ...</div>');
    $.post( "/gen-lineups", $('#frm-player').serialize(), function( data ) {
      $( "#div-result" ).html( data );
    });
  });

  $('.btn-clear').click(function() {
    $('#div-result').html('');
  });

  filterTable = function () {
    var position = $('.position-filter .nav-item a.active').html(),
        keyword = $('#search-player').val().toLowerCase().trim();    

    if (position == 'All') {
      position = '';
    }

    $("#div-players tr").filter(function() {
      $(this).toggle($(this).find('td:nth-child(2)').text().indexOf(position) > -1 && $(this).find('td:nth-child(3)').text().toLowerCase().indexOf(keyword) > -1)
    });

    $("#div-players thead tr").filter(function() {
      $(this).toggle(true);
    });
  }

  // filter players
  $("#search-player").on("keyup", function() {
    filterTable();
  });  

  $("#search-player").on("search", function() {
    filterTable();
  });

  $('.position-filter .nav-item a').on('click', function() {
    $('.position-filter .nav-item a').removeClass('active');
    $(this).toggleClass('active');
    filterTable();
  })
})

function pr_click(obj) {
  var checked = $(obj).parent().find('input').prop("checked");
  $(obj).parent().find('input').prop("checked", !checked);
}

function choose_all (obj) {
  $('input[type="checkbox"]').prop("checked", $(obj).prop('checked'));
}

function change_point (obj) {
  var pid = $(obj).data('id'),
      val = $(obj).val();
  $.post( "/update-point", { pid: pid, val: val }, function( data ) {})
}

function getPlayers () {
  var games = '';
  $('.slate').find('input:checked').each(function() {
    games += $(this).val()+';';
  })

  var ds = $('.nav-tabs.ds .nav-link.active').text();
  $.post( "/get-players", 
    { 
      ds: ds,
      games: games
    }, 
    function( data ) {
      $( "#div-players" ).html( data );
    }
  );
}  

function toggleLock(obj, pid) {
  if ($('.fa-lock').length == 7 && $(obj).hasClass('fa-lock-open')) {
    alert('You cannot add more locked players.');
    return false;
  }

  $(obj).toggleClass('fa-lock-open');
  $(obj).toggleClass('fa-lock');

  if ($(obj).hasClass('fa-lock')) {
    $('#frm-player').append(`<input type="hidden" name="locked" value="${pid}" id="lock${pid}">`);
  } else {
    $(`#lock${pid}`).remove();
  }
}
