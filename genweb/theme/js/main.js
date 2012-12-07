// En aquest script agruparem tots els "document ready"

$(document).ready(function () {

  // custom file input, checkboxes i radios
  $('[type=file]').customFileInput();
  $('select').dropkick();
  $('ul.dk_options_inner').addClass('scrollable');
  if ($(window).width() < 640 ) {
    $(document).scrollTop( $("#portal-column-content").offset().top );
  }
  $('[type="checkbox"]').customInput();
  $('[type="radio"]').customInput();

  // inicialitzacions dels tooltips i popovers
  $('[rel="tooltip"]').tooltip();
  $('[rel="popover"]').popover();

  // animacions varies
  $(document).on('touchend click', '.amunt a', function() {
    $("html, body").animate({ scrollTop: 0 }, 'slow');
  });

  // 'nou' badge
  $('.dropdown:has(.badge)').addClass('nou');

  // ReView inicialitzacions
  $('.userScreen').click(function() {
    $('html').removeClass('simulated-mobile-view');
    $('html').removeClass('simulated-tablet-view');
    $("#portal-column-content").getNiceScroll().hide();
  });
  $('.userTablet').click(function() {
    $('html').removeClass('simulated-mobile-view');
    $('html').addClass('simulated-tablet-view');
    $("#portal-column-content").getNiceScroll().show();
    $("html.simulated-tablet-view #portal-column-content").niceScroll({touchbehavior:false,cursorcolor:"#000",cursoropacitymax:0.75,cursoropacitymin: 0.25,cursorwidth:6});
  });
  $('.userMobile').click(function() {
    $('html').removeClass('simulated-tablet-view');
    $('html').addClass('simulated-mobile-view');
    $("#portal-column-content").getNiceScroll().show();
    $("html.simulated-mobile-view #portal-column-content").niceScroll({touchbehavior:false,cursorcolor:"#000",cursoropacitymax:0.75,cursoropacitymin: 0.25,cursorwidth:6});
  });
});
