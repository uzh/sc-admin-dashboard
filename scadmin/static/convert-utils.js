function BtoH(bytes) {
    var i = -1;
    if(bytes<0){
        bytes = Math.abs(bytes);
    }
    var byteUnits = [' KiB', ' MiB', ' GiB', ' TiB', 'PiB', 'EiB', 'ZiB', 'YiB'];
    do {
        bytes = bytes / 1024;
        i++;
    } while (bytes >= 1024);
    return Math.max(bytes, 0).toFixed(2) + byteUnits[i];
}

function SignedBtoH(bytes){
    var val = BtoH(bytes);
    if (bytes >= 0) {
        return "+" + val;
    } else {
        return "-" + val;
    }
}

function GBtoH(gb){return BtoH(gb*Math.pow(2,30));}
function MBtoH(mb){return BtoH(mb*Math.pow(2,20));}
    
function HtoB(input){
    var validAmount  = function(n) {
        return !isNaN(parseFloat(n)) && isFinite(n);
    };

    var parsableUnit = function(u) {
        return u.match(/\D*/).pop() === u;
    };

    var incrementBases = {
        2: [
            [["b", "bits"], 1/8],
            [["B", "Bytes"], 1],
            [["Kb"], 128],
            [["k", "K", "kb", "KB", "KiB", "kib", "Kib", "Ki", "ki"], 1024],
            [["Mb"], 131072],
            [["m", "M", "mb", "MB", "MiB", "mib", "Mib", "Mi", "mi"], Math.pow(1024, 2)],
            [["Gb"], 1.342e+8],
            [["g", "G", "gb", "GB", "GiB", "gib", "Gib", "Gi", "gi"], Math.pow(1024, 3)],
            [["Tb"], 1.374e+11],
            [["t", "T", "tb", "TB", "TiB", "tib", "Tib", "Ti", "ti"], Math.pow(1024, 4)],
            [["Pb"], 1.407e+14],
            [["p", "P", "pb", "PB", "PiB", "pib", "Pib", "Pi", "pi"], Math.pow(1024, 5)],
            [["Eb"], 1.441e+17],
            [["e", "E", "eb", "EB", "EiB", "eib", "Eib", "Ei", "ei"], Math.pow(1024, 6)]
        ],
        10: [
            [["b", "bits"], 1/8],
            [["B", "Bytes"], 1],
            [["Kb"], 125],
            [["k", "K", "kb", "KB", "KiB", "kib", "Kib", "Ki", "ki"], 1000],
            [["Mb"], 125000],                            
            [["m", "M", "mb", "MB", "MiB", "mib", "Mib", "Mi", "mi"], 1.0e+6],
            [["Gb"], 1.25e+8],                           
            [["g", "G", "gb", "GB", "GiB", "gib", "Gib", "Gi", "gi"], 1.0e+9],
            [["Tb"], 1.25e+11],                          
            [["t", "T", "tb", "TB", "TiB", "tib", "Tib", "Ti", "ti"], 1.0e+12],
            [["Pb"], 1.25e+14],                          
            [["p", "P", "pb", "PB", "PiB", "pib", "Pib", "Pi", "pi"], 1.0e+15],
            [["Eb"], 1.25e+17],                          
            [["e", "E", "eb", "EB", "EiB", "eib", "Eib", "Ei", "ei"], 1.0e+18]
        ]
    };

    var options = arguments[1] || {};
    var base = parseInt(options.base || 2);

    var parsed = input.toString().match(/^([0-9\.,]*)(?:\s*)?(.*)$/);
    var amount = parsed[1].replace(',','.');
    var unit = parsed[2];

    var validUnit = function(sourceUnit) {
        return sourceUnit === unit;
    };

    if (!validAmount(amount) || !parsableUnit(unit)) {
        return 'Can\'t interpret ' + (input || 'a blank string');
    }
    if (unit === '') return Math.round(Number(amount));

    var increments = incrementBases[base];
    for (var i = 0; i < increments.length; i++) {
        var _increment = increments[i];

        if (_increment[0].some(validUnit)) {
            return Math.round(amount * _increment[1]);
        }
    }

    return unit + ' doesn\'t appear to be a valid unit';
    
}

function registerConverter(id){
    $(id+'_human').val(BtoH($(id).val()));
    $(id+'_human').keyup(function(event){
        var val = HtoB($(id+'_human').val());
        $(id).val(val);
        var cur = $(id+'_old').attr('cur');
        var delta = val-cur;
        $(id+'_old').text(SignedBtoH(delta))
        $(id+'_old').attr('delta', delta)
    });
}
