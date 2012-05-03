jq(function($) {

    var COMMUNICATION_ERROR = 'An error occured.';
    var MORE_TEXT = 'More...';
    var MAINTENANCE_ERROR = 'The source system is beeing maintained.';
    var NO_RESULTS = 'No results.';

    if ($('html').attr('lang') == 'de') {
        COMMUNICATION_ERROR = 'Ein unbekannter Fehler ist aufgetreten.';
        MORE_TEXT = 'Mehr...';
        MAINTENANCE_ERROR = 'Das Quellsystem ist wegen Wartungsarbeiten momentan nicht erreichbar.';
        NO_RESULTS = 'Keine Treffer';
    }

    var generate_item_nodes = function(items, callback) {
        return $(items).each(function() {
            var $item = $('<span class="title">');

            if(this.url) {
                var $link = $('<a>' + this.title + '</a>');
                $link.attr('class', this.cssclass);
                $link.attr('href', this.url);
                this.target && $link.attr('target', this.target);
                $link.appendTo($item);

            } else {
                $('<span class="' + this.cssclass + '">' +
                  this.title + '</span>').appendTo($item);
            }

            if(this.modified) {
                $('<span class="itemModified" />').text(
                    ' ' + this.modified).appendTo($item);
            }

            callback($item);
        });
    };

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

                } else if(data === 'MAINTENANCE') {
                    $portlet.find('.portletItem').html(
                        '<div class="error">'.concat(
                            MAINTENANCE_ERROR).concat('</div>'));

                } else {

                    $portlet.find('.portletItem').remove();

                    $portlet.find('.portletHeader .portlet-title').text(
                        data.title);

                    if (typeof(data.items) == 'undefined' || data.items.length === 0) {

                        $('<dd class="portletItem" />').text(NO_RESULTS).appendTo($portlet);

                    } else if (data.mode === 'ul') {

                        var $list = $('<ul>')
                          .appendTo($('<dd class="portletItem">')
                                    .appendTo($portlet));

                        generate_item_nodes(data.items, function(node) {
                            node.appendTo($('<li>').appendTo($list));
                        });


                    } else {
                        var odd = true;
                        generate_item_nodes(data.items, function(node) {
                            var cssclass = 'portletItem '.concat(
                                odd ? 'odd' : 'even');
                            odd = !odd;
                            node.appendTo(
                                $('<dd class="' + cssclass + '" />')
                                  .appendTo($portlet));
                        });
                    }

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
