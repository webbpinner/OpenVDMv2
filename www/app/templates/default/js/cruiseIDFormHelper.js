$(function () {
	'use strict';

	$('select[name=cruiseID]').change(function () {
		$("input[name=cruiseStartDate]").prop('disabled', true);
		$("input[name=cruiseEndDate]").prop('disabled', true);
    });

	$('input[name=cruiseStartDate]').on('input', function () {
		$("select[name=cruiseID]").prop('disabled', true);
	});

	$('#cruiseStartDate').on('dp.change', function () {
		$("select[name=cruiseID]").prop('disabled', true);
	});

	$('input[name=cruiseEndDate]').on('input', function () {
		$("select[name=cruiseID]").prop('disabled', true);
	});

	$('#cruiseEndDate').on('dp.change', function () {
		$("select[name=cruiseID]").prop('disabled', true);
	});

})