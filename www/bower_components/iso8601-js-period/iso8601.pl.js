/**
 * Polish translation for iso8601-js-period
 * Published under [Apache 2.0 license](http://www.apache.org/licenses/LICENSE-2.0.html)
 * ©author Piotr Grzelka <info@codeexpert.pl>
 */

nezasa.iso8601.Period._parseToString = nezasa.iso8601.Period.parseToString;
nezasa.iso8601.Period.parseToString = function(period, unitNames, unitNamesPlural, distributeOverflow) {

    if (!unitNames)       unitNames       = ['rok', 'miesiąc', 'tydzień', 'dzień', 'godzina', 'minuta', 'sekunda'];
    if (!unitNamesPlural) unitNamesPlural = ['lata', 'miesiące', 'tygodnie', 'dni', 'godziny', 'minuty', 'sekundy'];

    return nezasa.iso8601.Period._parseToString(period, unitNames, unitNamesPlural, distributeOverflow);
};