class Utils {
  convertFromSeconds(totalSeconds) {
    var hours, minutes, seconds;
    hours = Math.floor(totalSeconds / 3600);
    totalSeconds %= 3600;
    minutes = Math.floor(totalSeconds / 60);
    seconds = totalSeconds % 60;
    hours = hours < 10 ? "0" + hours : hours;
    minutes = minutes < 10 ? "0" + minutes : minutes;
    seconds = seconds < 10 ? "0" + seconds : seconds;
    return hours + ":" + minutes + ":" + seconds;
  }

  convertToSeconds(time) {
    var seconds;
    try {
      time = time.split(":");
      var hh = parseInt(time[0]);
      var mm = parseInt(time[1]);
      var ss = parseInt(time[2]);
      seconds = hh * 3600 + mm * 60 + ss;
    } catch(e) {
      seconds = 0
    }
    return seconds;
  }
}

export default new Utils();
