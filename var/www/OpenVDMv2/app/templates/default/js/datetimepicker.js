    var today = moment().set({'hour': 0, 'minute': 0, 'second': 0, 'millisecond': 0});

    $('#datetimepicker').datetimepicker({
        defaultDate: today,
        sideBySide: true,
        stepping: 15,
        format: 'YYYY/MM/DD HH:mm'
    });
