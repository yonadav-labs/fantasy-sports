var ds = 'DraftKings',
    bid = '';

$(function() {
  // when change slate
  $('body').on('change', '.slate input', function() {   // game slates checkbox
    getPlayers('-');
  });

  // change tab
  $('.nav-tabs.ds .nav-link').click(function () {
    ds = $(this).text();
    $('#ds').val(ds);
    getGames();
    // remove locked and clear search
    $('input[name=locked]').remove();
    $("#search-player").val('');
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
  });

  // sort
  $('#div-players').on('click', 'th.sort-col', function() {
    getPlayers($(this).data('order'));
  })
})

$("body").on('shown.bs.collapse', ".collapse", function() {
  bid = $(this).attr("id");
  build_lineup(null);
});

$("body").on('hidden.bs.collapse', ".collapse", function() {
  $(this).html("");
});

function build_lineup(pid) {
  $.post( "/build-lineup", {
    pid: pid,
    ds: ds,
    idx: bid.replace('collapse_', ''),
    ids: $('#frm-player').serialize()
  }, function( data ) {
    $("#"+bid).html(data.html);
    $('.fas.lock').removeClass('fa-lock');
    $('.fas.lock').addClass('fa-lock-open');

    for (ii in data.pids) {
      $(`.plb-${data.pids[ii]}`).toggleClass('fa-lock-open');
      $(`.plb-${data.pids[ii]}`).toggleClass('fa-lock');
    }

    if (data.msg) {
      alert(data.msg);
    }
  });
}

function add_lineup_(n) {
  nl_content = '<div class="card"> \
                  <div class="card-header"> \
                    <a class="card-link" href="#" onclick="$(\'#collapse_@@@\').collapse(\'show\')"> \
                      Lineup @@@ \
                    </a> \
                  </div> \
                  <div id="collapse_@@@" class="collapse" data-parent="#accordion"></div> \
                </div>';

  $('#accordion').append(nl_content.replace(/@@@/g, n));
}

function add_lineup() {
  num_lineups += 1;
  add_lineup_(num_lineups);
  $('#collapse_'+num_lineups).collapse('show');
}

function clear_lineup() {
  $('#accordion').html('');
  build_lineup(123456789);
  num_lineups = 0;
  add_lineup();
}

function init_lineups() {
  // add default lineups
  $('#accordion').html('');
  for (i = 0; i < num_lineups; i++) {
    add_lineup_(i+1);
  }
  $("#collapse_1").collapse('show');
}

function pr_click(obj) {
  var checked = $(obj).parent().find('input').prop("checked");
  $(obj).parent().find('input').prop("checked", !checked);
}

function choose_all (obj) {
  $('input[type="checkbox"]').prop("checked", $(obj).prop('checked'));
}

function change_point (obj, clear) {
  var pid = $(obj).data('id') * clear,
      val = $(obj).val();
  $.post( "/update-point", 
    { pid: pid, val: val },
    function( data ) {
      $(obj).closest('tr').find('td.pt-sal').html(data.pt_sal);
      if (clear < 0) {
        $(obj).closest('tr').removeClass('custom');
        $(obj).val(data.points);
      } else {
        $(obj).closest('tr').addClass('custom');
      }
    });
}

function clear_proj (obj) {
  change_point($(obj).prev(), -1);
}

function getGames() {
  $.post( "/get-slates", 
    { 
      ds: ds
    }, 
    function( data ) {
      $( "div.slate" ).html( data );
      getPlayers();
    }
  );
}

function getPlayers (order) {
  var games = '';
  $('.slate').find('input:checked').each(function() {
    games += $(this).val()+';';
  })

  $.post( "/get-players", 
    { 
      ds: ds,
      games: games,
      order: order
    }, 
    function( data ) {
      $( "#div-players" ).html( data.html );
      filterTable();  // reapply position filter

      var is_optimizer = $('#div-result').length > 0;

      if (!order) {
        if (is_optimizer) {
          $('#div-result').html('');
        } else {
          num_lineups = data.num_lineups;
          init_lineups();
        }
      } else if (!is_optimizer) {
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
  $.post( "/check-mlineups", 
    { 
      ds: ds,
    }, 
    function( data ) {
      $('#dlg-export .modal-body').html('');
      for (ii in data) {
        cb_content = '<div class="form-check @@@"> \
                        <label class="form-check-label"> \
                          <input type="checkbox" name="lidx" class="form-check-input" value="IDX" @@@>Lineup IDX \
                        </label> \
                      </div>';
        $('#dlg-export .modal-body').append(cb_content.replace(/IDX/g, data[ii][0]).replace(/@@@/g, data[ii][1]));
      }
      $('#dlg-export').modal();
    }
  );

  return false;
}