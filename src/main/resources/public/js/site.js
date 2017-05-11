$(document).ready(function () {

    // Progressiriba
    var loader = new ProgressBar.Circle(container, {
        color: '#333',
        strokeWidth: 10,
        trailWidth: 5,
        text: {
            autoStyleContainer: false
        },
        from: {color: '#fff', width: 4},
        to: {color: '#fff', width: 4},
        step: function (state, circle) {
            circle.path.setAttribute('stroke', state.color);
            circle.path.setAttribute('stroke-width', state.width);

            var value = Math.round(circle.value() * 100);
            if (value === 0) {
                circle.setText('0%');
            } else {
                circle.setText(" " + value + "%");
            }

        }
    });

    // Teksti sisestamise vorm
    var frm = $('#simplify_form');

    /* Kui kasutaja vajutab "Lihtsusta" nuppu, saadame päringu tagasüsteemile */
    frm.submit(function (ev) {
        document.getElementById("submit").disabled = true;
        startLoader(calculateEstimatedTime());
        $.ajax({
            type: frm.attr('method'),
            url: frm.attr('action'),
            data: frm.serialize(),
            success: function (data) {
                document.getElementById("submit").disabled = false;
                setText(data);
                endLoader();
            }
        });

        ev.preventDefault();
    });

    /* Kuvame tagarakenduselt saadud teksti kasutajale */
    function setText(data) {
        data = data.replace(/(?:\r\n*|\r|\n)/g, '<br />');
        var regex = /\${(.*?)}\$/g;
        var myArray = data.match(regex);
        document.getElementById("result").innerHTML = "";

        if (myArray == null) {
            document.getElementById("result").innerHTML = data;
            console.log(data);
            return;
        }
        for (var i = 0; i < myArray.length; i++) {
            var word = myArray[i].replace(regex, '$1');
            var words = word.split(',');
            if (words.length > 1) {
                var newDiv = '<div class="dropdown"><span id="display-' + (i + 1) + '" onclick="myFunction(' + (i + 1) +
                    ')" class="dropbtn">' + words[0] +
                    '</span><div id="myDropdown-' + (i + 1) + '" class="dropdown-content">';
                // var newDiv = "<span class='replaced_multiple'>";
                for (var j = 0; j < words.length; j++) {
                    // newDiv += "<span class='replaced_item'>" + words[j] + "</span>";
                    newDiv += '<span onclick="changeDisplayText(' + (i + 1) + ',\'' + words[j] + '\')">' + words[j] + '</span>';
                }
                // newDiv += "</span>"
                newDiv += "</div></div>";

                data = data.replace(myArray[i], newDiv)
            } else {
                data = data.replace(myArray[i], "<span class='replaced_single'>" + words[0] + "</span>")
            }
        }

        console.log(data);
        document.getElementById("result").innerHTML = data
    }

    /* Kuvame progressiriba */
    function startLoader(timer) {
        $("#container").fadeIn("fast");
        loader.animate(1.0, {
            duration: timer
        });
    }

    /* Peidame progressiriba */
    function endLoader() {
        loader.animate(1.0, {
            duration: 100
        });
        $("#container").fadeOut("fast", function () {
            loader.set(0);
        });
    }


    /* Arvutamine hinnangulise ooteaja */
    function calculateEstimatedTime() {
        var user_input_length = $("#entered").val().split(/[\s,.!?]+/).length;
        var empty_input_time = 8000;
        var threshold = document.getElementById("threshold").value;

        return empty_input_time + user_input_length * 25 + threshold * user_input_length * 0.3;
    }

    /* Lävendi arvu valik */
    var rangeSlider = function () {
        var slider = $('.range-slider'),
            range = $('.range-slider__range'),
            value = $('.range-slider__value');

        slider.each(function () {

            value.each(function () {
                var value = $(this).prev().attr('value');
                $(this).html(value);
            });

            range.on('input', function () {
                $(this).next(value).html(this.value);
            });
        });
    };
    rangeSlider();

});


/* When the user clicks on the button, toggle between hiding and showing the dropdown content */
function myFunction(id) {
    document.getElementById("myDropdown-" + id).classList.toggle("show");
}
function changeDisplayText(id, text) {
    document.getElementById("display-" + id).innerHTML = text
}

// Sulgeme sõnade kuvamise menüü
window.onclick = function (event) {
    if (!event.target.matches('.dropbtn')) {

        var dropdowns = document.getElementsByClassName("dropdown-content");
        var i;
        for (i = 0; i < dropdowns.length; i++) {
            var openDropdown = dropdowns[i];
            if (openDropdown.classList.contains('show')) {
                openDropdown.classList.remove('show');
            }
        }
    }
};
