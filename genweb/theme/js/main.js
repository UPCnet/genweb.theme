// En aquest script agruparem tots els "document ready"

$(document).ready(function () {
  $('[type=file]').customFileInput();
  // $('select:not([multiple])').dropkick();
  $('ul.dk_options_inner').addClass('scrollable');
  if ($(window).width() < 640 ) {
    $('.nav-tabs').addClass('nav-stacked');
    $('.nav-pills').addClass('nav-stacked');
    $(document).scrollTop( $("content").offset().top );
  }
  $('.custom-chekbox[type="checkbox"]').customInput();
  $('.custom-radio[type="radio"]').customInput();

  $('[rel="tooltip"]').tooltip();
  $('[rel="popover"]').popover();
  $(document).on('touchend click', '.amunt a', function() {
    $("html, body").animate({ scrollTop: 0 }, 'slow');
  });
  $('.dropdown:has(.badge)').addClass('nou');
  $('ul.dropdown-menu li:has(.actionMenuSelected)').addClass('active');

  $('.userScreen').click(function() {
    $('html').removeClass('simulated-mobile-view');
    $('html').removeClass('simulated-tablet-view');
    $("#content").getNiceScroll().hide();
    $("#content").css({ overflow: "visible" }); //fixa bug de l'scroll
  });
  $('.userTablet').click(function() {
    $("#content").css({ overflow: "hidden" }); //fixa bug de l'scroll
    $('html').removeClass('simulated-mobile-view');
    $('html').addClass('simulated-tablet-view');
    $("html.simulated-tablet-view #content").niceScroll({touchbehavior:false,cursorcolor:"#000",cursoropacitymax:0.75,cursoropacitymin: 0.25,cursorwidth:6});
    $("html.simulated-tablet-view #content").getNiceScroll().show();
    $("#content").getNiceScroll().resize();
  });
  $('.userMobile').click(function() {
    $("#content").css({ overflow: "hidden" }); //fixa bug de l'scroll
    $('html').removeClass('simulated-tablet-view');
    $('html').addClass('simulated-mobile-view');
    $("html.simulated-mobile-view #content").niceScroll({touchbehavior:false,cursorcolor:"#000",cursoropacitymax:0.75,cursoropacitymin: 0.25,cursorwidth:6});
    $("html.simulated-mobile-view #content").getNiceScroll().show();
    $("#content").getNiceScroll().resize();
  });

  var prettify = false;
  $("pre").each(function() {
      $(this).prepend('<code>');
      $(this).append('</code>');
      $(this).addClass('prettyprint linenums');
      prettify = true;
  });

  if ( prettify ) {
      $.getScript("/++genweb++static/js/prettify.js", function() { prettyPrint() });
  }

 $("#cercaCapca").typeahead({
   source: function (query, process) {
      setTimeout(searchElements(query, process) , 300);
   }
   , highlighter: function(item){
      info = items[item.split("#")[0]];
      var itm = ''
               + "<div class='typeahead_wrapper'>"
               + "<i class='icon-"+info.icon+"'> </i>"
               + "<class='typeahead_primary'>"+info.tittle+"</div>"
               + "<div class='typeahead_secondary'>"+info.description+"</div>"
               + "</div>";
      return itm;
  }
  , matcher: function (item) {
       return ~item.split("#")[0].toLowerCase().indexOf(this.query.toLowerCase()) || item.split("#")[0].toLowerCase() == "advanced search"
  }
  , updater: function(item) {
      window.location.href = item.split("#")[1];
  }
  , items: 10
  , minLength: 2
  });

 var searchElements = function( query, process ){
     $.get(document.getElementsByTagName('base')[0].href+"/typeaheadJson", { q: query }, function(data) {
          //Reseting containers
          items = {};
          info  = [];

          var i = 0
          $.each(data, function(i) {
              items[data[i]['tittle']] = {'tittle': data[i]['tittle'], 'description': data[i]['description'], 'itemUrl': data[i]['itemUrl'],  'icon': data[i]['icon']};
              info.push(data[i]['tittle']+"#"+data[i]['itemUrl']);
              ++i;
          });
          process(info);

    });
 };

});
