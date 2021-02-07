    var today = moment().set({'hour': 0, 'minute': 0, 'second': 0, 'millisecond': 0});
    var now = moment().set({'minute': 0, 'second': 0, 'millisecond': 0});

    $('.datetimepicker').datetimepicker({
        sideBySide: true,
        stepping: 15,
        format: 'YYYY/MM/DD HH:mm'
    });

    $('.datetimepickerToday').datetimepicker({
        defaultDate: today,
        sideBySide: true,
        stepping: 15,
        format: 'YYYY/MM/DD HH:mm'
    });

    $('.datetimepickerNow').datetimepicker({
        defaultDate: now,
        sideBySide: true,
        stepping: 15,
        format: 'YYYY/MM/DD HH:mm'
    });