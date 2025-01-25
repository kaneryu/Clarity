function addAlpha(alpha, color) {
    let c = color
    // remove the # from the color
    c = c.slice(1)
    // add the alpha value 
    c = "#" + alpha + c
    return c
}

function secondsToHMS(seconds) {
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