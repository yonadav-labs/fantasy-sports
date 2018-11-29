var ds = 'DraftKings';

$(function() {
  $('.slate input').on('change', function() {   // game slates checkbox
    getPlayers();
  });

  $('.nav-tabs.ds .nav-link').click(function () {
    ds = $(this).text();
    $('#ds').val(ds);
    // getPlayers();
  });

  $('.nav-tabs.ds .nav-link:first').click();

  $('.btn-export').click(function(e) {
    if (e) {
      e.preventDefault();
    }
    var num_players = $('input[type="checkbox"]:checked').length;
    if (num_players == 0) {
      alert('Please choose players.');
      return false;
    }

    $('#frm-player').submit();
    $('#dlg-export').modal();
  });

  $('.btn-calc').click(function() {
    var num_players = $('input[type="checkbox"]:checked').length;
    if (num_players < 8) {
      alert('Please choose more than 8 players.');
      return
    }

    $('#div-result').html('<div class="font-weight-bold text-center" style="margin-top: 64px; min-height: 108px;">Calculating ...</div>');
    $.post( "/gen-lineups", $('#frm-player').serialize(), function( data ) {
      $("#div-result").html(data.player_stat);
      $('#dlg-preview .modal-body').html(data.preview_lineups);
      $('#dlg-preview').modal();
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

function build_lineup(pid) {
  $.post( "/build-lineup", {
    pid: pid,
    ds: ds
  }, function( data ) {
    $("#div-lineup").html(data.html);
    $('.fas.lock').removeClass('fa-lock');
    $('.fas.lock').addClass('fa-lock-open');

    for (ii in data.pids) {
      console.log(`.plb-${data.pids[ii]}`);
      $(`.plb-${data.pids[ii]}`).toggleClass('fa-lock-open');
      $(`.plb-${data.pids[ii]}`).toggleClass('fa-lock');
    }

    if (data.msg) {
      alert(data.msg);
    }
  });
}

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

  $.post( "/get-players", 
    { 
      ds: ds,
      games: games
    }, 
    function( data ) {
      $( "#div-players" ).html( data );
      
      if ($('#div-result').length > 0) {  // optimizer
        $('#div-result').html('');
      } else {
        build_lineup(null);
      }
    }
  );
}  

function toggleLock(obj, pid) {
  if ($('#div-lineup').length > 0) {    // lineup builder
    if ($(obj).hasClass('fa-lock')) {
      pid = -pid;
    }

    build_lineup(pid);
  } else {
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
}

function export_lineup(e) {
  e.preventDefault();
  location.href = '/export-manual-lineup'; 
  return false;
}