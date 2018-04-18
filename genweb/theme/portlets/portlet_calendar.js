(function ($) {

    function load_portlet_calendar(event, elem) {
        // depends on plone_javascript_variables.js for portal_url
        event.preventDefault();
        var pw = elem.closest('.portletWrapper');
        var elem_data = elem.data();
        var portlethash = pw.attr('id');
        portlethash = portlethash.substring(15, portlethash.length);
        var comnunity = $('#box_agenda')
        var is_community = comnunity.length > 0
        var base_url = portal_url + '/' + $('html').attr('lang') + '/'
        if (is_community)
            base_url = $('head base').attr('href')

        url = base_url +
              '/@@render-portlet?portlethash=' + portlethash +
              '&year=' + elem_data.year +
              '&month=' + elem_data.month;
        $.ajax({
            url: url,
            success: function (data) {
                pw.html(data);
                rebind_portlet_calendar();
            }
        });
    }

    function rebind_portlet_calendar() {
        // ajaxify each portletCalendar
        $('.portletCalendar a.calendarNext').click(function (event) {
            load_portlet_calendar(event, $(this));
        });
        $('.portletCalendar a.calendarPrevious').click(function (event) {
            load_portlet_calendar(event, $(this));
        });
        $('.portletCalendar dd a[title]').tooltip({
            offset: [-10, 0],
            tipClass: 'pae_calendar_tooltip'
        });
        try {
            $('[rel="popover"]').popover();
        }
        catch (e) {
            console.log('This instance seems that doesn\'t have bootstrap.popover loaded')
        }
        // Prevent click on calendar events to allow popover
        $('.cal_has_events').click(function (event) {
            event.preventDefault();
            $('.popover-content').off('click').on('click', 'a' , function() {
                window.location=this.href;
             });

        });
    }

    $(document).ready(function () {
        rebind_portlet_calendar();
    });

}(jQuery));
