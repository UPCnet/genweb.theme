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
      $.getScript("/++genweb++static/js/prettify.js", function() {prettyPrint()});
  }


// Live search

 $("#cercaCapca").typeahead({
   source: function (query, process) {
      setTimeout(searchElements(query, process) , 300);
   },
   highlighter: function(item){
      var iitem = $("#cercaCapca").get(0).results[item];
      //info = items[item.split("#")[0]];
      var itm = "<i class='icon-"+iitem.icon+"'></i> " +
                 iitem.title +
                "<p class='xs margin0'>"+iitem.description+"</p>";
      return itm;
  },
  matcher: function (item) {
      return true;
  },
  updater: function(item) {
      window.location.href = $("#cercaCapca").get(0).results[item]['itemUrl'];
  },
  items: 12,
  minLength: 2
  });

 var searchElements = function( query, process ){
     $.get(document.getElementsByTagName('base')[0].href+"/typeaheadJson", { q: query }, function(data) {
          //Reseting containers
          var items = [];

          $.each(data, function(index, value) {
              items.push(index.toString());
          });
          $("#cercaCapca").get(0).results = data;
          process(items);
    });
 };


// Favorites
$('.favorite').on('click', function(event) {
  event.preventDefault();
  var community_url = $(this).data()['community'];
  $.get(community_url + '/toggle-favorite');
  if ($('i', this).hasClass('fa-icon-star')) {
    $('i', this).addClass('fa-icon-star-empty').removeClass('fa-icon-star');
  } else {
    $('i', this).addClass('fa-icon-star').removeClass('fa-icon-star-empty');
  }
});

});
