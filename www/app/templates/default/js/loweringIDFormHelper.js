$(function () {
	'use strict';

	$('select[name=loweringID]').change(function () {
		$("input[name=loweringStartDate]").prop('disabled', true);
		$("input[name=loweringEndDate]").prop('disabled', true);
    });

	$('input[name=loweringStartDate]').on('input', function () {
		$("select[name=loweringID]").prop('disabled', true);
	});

	$('#loweringStartDate').on('dp.change', function () {
		$("select[name=loweringID]").prop('disabled', true);
	});

	$('input[name=loweringEndDate]').on('input', function () {
		$("select[name=loweringID]").prop('disabled', true);
	});

	$('#loweringEndDate').on('dp.change', function () {
		$("select[name=loweringID]").prop('disabled', true);
	});

})