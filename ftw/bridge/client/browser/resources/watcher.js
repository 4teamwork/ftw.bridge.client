jq(function($) {

    var COMMUNICATION_ERROR = 'An error occured.';
    var MORE_TEXT = 'More...';

    if (document.all[0].lang == 'de') {
        COMMUNICATION_ERROR = 'Ein unbekannter Fehler ist aufgetreten.';
        MORE_TEXT = 'Mehr...';
    }

    $('.portletWatcher.portlet').each(function() {

        var $portlet = $(this);

        var wrapper = jq(this).parents(':first[id^=portletwrapper-]');
        var hash = wrapper[0].id.substr('portletwrapper-'.length);
        var url = portal_url.concat('/@@watcher-load-data').concat(
            '?hash=').concat(hash);

        $.ajax({
            type: 'GET',
            url: url,
            dataType: 'json',

            success: function(data) {
                if(typeof(data.error) !== 'undefined') {
                    $portlet.find('.portletItem').html(
                        '<div class="error">'.concat(data.error).concat(
                            '</div>'));
                } else {

                    $portlet.find('.portletItem').remove();

                    $portlet.find('.portletHeader .portlet-title').text(
                        data.title);

                    var odd = true;
                    $(data.items).each(function() {
                        var cssclass = 'portletItem '.concat(
                            odd ? 'odd' : 'even');
                        odd = !odd;

                        var item = $('<span class="title">').appendTo(
                            $('<dd class="' + cssclass + '" />').appendTo(
                                $portlet));

                        $('<a class="' + this.cssclass + '" ' +
                          'href="' + this.url +
                          '">' + this.title + '</a>'
                         ).appendTo(item);

                        $('<span class="portletItemDetails" />').text(
                            ' ' + this.modified).appendTo(item);
                    });

                    if(typeof(data.details_url) != 'undefined') {
                        $('<dd class="portletFooter" />')
                          .appendTo($portlet)
                          .append($('<a href="' + data.details_url + '">' +
                                    MORE_TEXT + '</a>'));
                    }
                }
            },

            error: function(jqXHR, textStatus, errorThrown) {
                $portlet.find('.portletItem').html(
                    '<div class="error">'.concat(COMMUNICATION_ERROR).concat(
                        '</div>'));
                if(typeof(console) != "undefined") {
                    console.error('Watcher portlet ERROR', jqXHR,
                                  textStatus, errorThrown);
                }
            }
        });

    });
});
