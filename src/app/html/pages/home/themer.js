var csstheme = document.querySelector(':root')


new QWebChannel(qt.webChannelTransport, function (channel) {
    window.backend = channel.objects.backend;
    window.theme = channel.objects.theme;
    theme.themeChanged.connect(changeTheme);
});

function setCssVariable(name, value) {
    csstheme.style.setProperty(name, value);
}

async function changeTheme() {
    let result = await theme.getAllColors();
    result = JSON.parse(result);
    for (let key in result) {
        setCssVariable("--" + key, result[key]);
    }
}

