$(document).ready(function () {
    var defaultReceiverType = $('#id_receiver_type').val() || "resident";
    loadUsers(defaultReceiverType);

    $('#id_receiver_type').change(function () {
        var receiverType = $(this).val();
        loadUsers(receiverType);
    });

    $('#id_send_all').change(function () {
        var $checkboxes = $('#user-list input[type="checkbox"]');
        $checkboxes.prop('checked', $(this).is(':checked'));
    });

    function loadUsers(receiverType) {
        $.ajax({
            url: loadUsersByRoleUrl,
            type: 'POST',
            data: {
                receiver_type: receiverType,
                csrfmiddlewaretoken: $('[name=csrfmiddlewaretoken]').val()
            },
            success: function (data) {
                var $tbody = $('#user-list');
                $tbody.empty();
                $.each(data.users, function (index, user) {
                    $tbody.append(
                        $('<tr>').append(
                            $('<td class="border text-center align-middle">').append(
                                $('<input>').attr({
                                    type: 'checkbox',
                                    name: 'receiver',
                                    value: user.id,
                                    class: 'mr-2'
                                })
                            ),
                            $('<td>').text(user.name).addClass('border p-2')
                        )
                    );
                });
                $('#id_send_all').prop('checked', false); // Reset checkbox
            }
        });
    }
});
