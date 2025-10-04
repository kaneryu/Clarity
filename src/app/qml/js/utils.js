function addAlpha(alpha, color) {
    let c = color
    // remove the # from the color
    c = c.slice(1)
    // add the alpha value 
    c = "#" + alpha + c
    return c
}

function secondsToHMS(seconds) {
    if (seconds <= 0 || isNaN(seconds)) {
        return '00:00'
    }

    let hours = Math.floor(seconds / 3600);
    let minutes = Math.floor((seconds % 3600) / 60);
    let secs = Math.floor(seconds % 60);

    let retlist = []

    if (hours > 0) {
        retlist.push(hours.toString().padStart(2, '0'))
    }
    retlist.push(minutes.toString().padStart(2, '0'))
    retlist.push(secs.toString().padStart(2, '0'))
    

    return retlist.join(':');
}

function albumTypeCorrector(type) {
    if (type.toLowerCase() === "album") {
        return "Album"
    } else if (type.toLowerCase() === "single") {
        return "Single"
    } else if (type.toLowerCase() === "ep") {
        return "EP"
    } else {
        return type
    }
}