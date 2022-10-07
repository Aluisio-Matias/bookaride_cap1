//delete displayed flash messages on the page by pressing the X button.
$('#flashMsg').on('click', '.delete-button', async function (evt) {
    evt.preventDefault();
    let $flashMsg = $(evt.target).closest("div");
    $flashMsg.remove();
})


// check if username already existis in the users database
$('#username').on('focusout', function () {
    $.getJSON("/check/" + $("#username").val(), (data) => {

        if (data['exists'] === true) {
            $("#checkUser").html("<i style='color:#4bbf73;' class='fa-solid fa-check fa-xl'></i><span class='badge rounded-pill bg-success'>This username is available!</span>");

        } else {
            $("#checkUser").html("<i style='color:#d9534f;' class='fa-solid fa-triangle-exclamation fa-xl'></i><span class='badge rounded-pill bg-danger'>This username is not available!</span>");
        }
    })
});

// check if phone number already existis in the users database
$('#phone').on('focusout', function () {
    $.getJSON("/verify/" + $("#phone").val(), (data) => {

        if (data['exists'] === true) {
            $("#phoneCheck").html("<i style='color:#4bbf73;' class='fa-solid fa-check fa-xl'></i>");

        } else {
            $("#phoneCheck").html("<i style='color:#d9534f;' class='fa-solid fa-triangle-exclamation fa-xl'></i><span class='badge rounded-pill bg-danger'>This phone number belongs to another user.</span>");
        }
    })
});

// check if email already existis in the users database
$('#email').on('focusout', function () {
    $.getJSON("/lookup/" + $("#email").val(), (data) => {

        if (data['exists'] === true) {
            $("#checkEmail").html("<i style='color:#4bbf73;' class='fa-solid fa-check fa-xl'></i>");

        } else {
            $("#checkEmail").html("<i style='color:#d9534f;' class='fa-solid fa-triangle-exclamation fa-xl'></i><span class='badge rounded-pill bg-danger'>This E-mail belongs to another user.</span>");
        }
    })
});

// check if username already existis in the admin database
$('#admin_username').on('focusout', function () {
    $.getJSON("/check_admin/" + $("#admin_username").val(), (data) => {

        if (data['exists'] === true) {
            $("#adminUser").html("<i style='color:#4bbf73;' class='fa-solid fa-check fa-xl'></i><span class='badge rounded-pill bg-success'>This username is available!</span>");

        } else {
            $("#adminUser").html("<i style='color:#d9534f;' class='fa-solid fa-triangle-exclamation fa-xl'></i><span class='badge rounded-pill bg-danger'>This username is not available!</span>");
        }
    })
});

// check if email already existis in the users database
$('#admin_email').on('focusout', function () {
    $.getJSON("/verify_admin/" + $("#admin_email").val(), (data) => {

        if (data['exists'] === true) {
            $("#adminEmail").html("<i style='color:#4bbf73;' class='fa-solid fa-check fa-xl'></i>");

        } else {
            $("#adminEmail").html("<i style='color:#d9534f;' class='fa-solid fa-triangle-exclamation fa-xl'></i><span class='badge rounded-pill bg-danger'>This E-mail belongs to another user.</span>");
        }
    })
});


// Mapquest place-search API for address input 
window.onload = function () {
    let ps = placeSearch({
        key: 'Ytg3hzPVuz5SkYxL04RbcLm2AZQrHGhm',
        container: document.querySelector('#PU_address'),
        useDeviceLocation: true,
        collection: [
            'poi',
            'airport',
            'address',
            'adminArea',
        ]

    });

    ps.on('change', (e) => {
        document.querySelector('#PU_street').value = e.result.name || '';
        document.querySelector('#PU_city').value = e.result.city || '';
        document.querySelector('#PU_state').value = e.result.stateCode || '';
        document.querySelector('#PU_zip').value = e.result.postalCode || '';
        document.querySelector('#PU_country').value = e.result.countryCode || '';
    });

    ps.on('clear', () => {
        document.querySelector('#PU_street').value = '';
        document.querySelector('#PU_city').value = '';
        document.querySelector('#PU_state').value = '';
        document.querySelector('#PU_zip').value = '';
        document.querySelector('#PU_country').value = '';
    });

    ps.on('error', (e) => {
        console.log(e);
    })

};
