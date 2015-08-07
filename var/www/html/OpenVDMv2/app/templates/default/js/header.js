$(function () {
    'use strict';
    
    function formatFilesize(bytes) {
        var s = ['bytes', 'kb', 'MB', 'GB', 'TB', 'PB'];
        var e = Math.floor(Math.log(bytes) / Math.log(1024));
        return (bytes / Math.pow(1024, Math.floor(e))).toFixed(2) + " " + s[e];
    }
    
    function timeElapsedString(mysqlTime) {

        var etime = Math.abs(new Date() - new Date(mysqlTime.replace(/ /g, 'T') + 'Z')) / 1000;
        if (etime < 1) {
            return '0 seconds ago';
        }

        var s = [{'math' : 365 * 24 * 60 * 60, 'single': 'year', 'plural': 'years'},
                 {'math' : 30 * 24 * 60 * 60, 'single': 'month', 'plural': 'months'},
                 {'math' : 24 * 60 * 60, 'single': 'day', 'plural': 'days'},
                 {'math' : 60 * 60, 'single': 'hour', 'plural': 'hours'},
                 {'math' : 60, 'single': 'minute', 'plural': 'minutes'},
                 {'math' : 1, 'single': 'second', 'plural': 'seconds'}];
        
        var i = 0;

        for (i = 0; i < s.length; i++) {
            var e = Math.floor(etime / s[i].math);
            if (e === 1) {
                return e + ' ' + s[i].single + ' ago';
            } else if (e >= 1) {
                return e + ' ' + s[i].plural + ' ago';
            }
        }
    }
    
    function updateSystemStatusPanel(systemStatusPanel, systemStatus) {
        var systemStatusURL = siteRoot + 'api/warehouse/getSystemStatus';
        $.getJSON(systemStatusURL, function (data, status) {
            if (status === 'success' && data !== null) {
                $(systemStatus).html(data.systemStatus);
                if (data.systemStatus === "On") {
                    $(systemStatus).html("On");
                    $(systemStatusPanel).removeClass('panel-primary');
                    $(systemStatusPanel).removeClass('panel-red');
                    $(systemStatusPanel).addClass('panel-green');
                } else if (data.systemStatus === "Off") {
                    $(systemStatus).html("Off");
                    $(systemStatusPanel).removeClass('panel-primary');
                    $(systemStatusPanel).removeClass('panel-green');
                    $(systemStatusPanel).addClass('panel-red');
                }
            }
            setTimeout(function () {
                updateSystemStatusPanel(systemStatusPanel, systemStatus);
            }, 5000);
        });
    }
    
    function updateCruiseSizePanel(cruiseSizePanel, cruiseSize) {
        var transferStatusURL = siteRoot + 'api/warehouse/getCruiseSize';
        $.getJSON(transferStatusURL, function (data, status) {
            if (status === 'success' && data !== null) {
                if (data.error) {
                    $(cruiseSize).html('Error');
                    $(cruiseSizePanel).removeClass('panel-primary');
                    $(cruiseSizePanel).addClass('panel-red');
                } else {
                    $(cruiseSize).html(formatFilesize(data.cruiseSize));
                    $(cruiseSizePanel).removeClass('panel-red');
                    $(cruiseSizePanel).addClass('panel-primary');
                }
            }
            setTimeout(function () {
                updateCruiseSizePanel(cruiseSizePanel, cruiseSize);
            }, 5000);
        });
    }
    
    function updateFreeSpacePanel(freeSpacePanel, freeSpace) {
        var transferStatusURL = siteRoot + 'api/warehouse/getFreeSpace';
        $.getJSON(transferStatusURL, function (data, status) {
            if (status === 'success' && data !== null) {
                if (data.error) {
                    $(freeSpace).html('Error');
                    $(freeSpacePanel).removeClass('panel-primary');
                    $(freeSpacePanel).addClass('panel-red');
                } else {
                    $(freeSpace).html(formatFilesize(data.freeSpace));
                    $(freeSpacePanel).removeClass('panel-red');
                    $(freeSpacePanel).addClass('panel-primary');
                }
            }
            setTimeout(function () {
                updateFreeSpacePanel(freeSpacePanel, freeSpace);
            }, 5000);
        });
    }
    
    function updateMessageCount(OVDM_messageCount) {
        var getNewMessageCount = siteRoot + 'api/messages/getNewMessagesTotal';
        $.getJSON(getNewMessageCount, function (data, status) {
            if (status === 'success' && data !== null) {
                $(OVDM_messageCount).html(data);
            }
            setTimeout(function () {
                updateMessageCount(OVDM_messageCount);
            }, 5000);
        });
    }
    
    function updateRecentMessages(OVDM_messagesUI, OVDM_messageCount) {
        var getRecentMessagesURL = siteRoot + 'api/messages/getRecentMessages';
        $.getJSON(getRecentMessagesURL, function (data, status) {
            if (status === 'success' && data !== null) {
                var ul = document.createElement("ul");
                ul.setAttribute("class", "dropdown-menu dropdown-alerts");
                ul.setAttribute("id", "OVDM_messages");

                var index;
                for (index = 0; index < data.length; index++) {
                    var timeAgo = timeElapsedString(data[index]['messageTS']);

                    
                    var sp = document.createElement('span');
                    sp.setAttribute("class", "pull-right text-muted small");
                    sp.innerHTML = timeAgo;

                    var s = document.createElement('strong');
                    s.innerHTML = data[index]['message'];
                    s.appendChild(sp);
                    
                    var a = document.createElement('a');
                    a.setAttribute("class", "OVDM_message");
                    a.setAttribute("messageID", data[index]['messageID']);
                    a.setAttribute("href", "#");
                    a.appendChild(s);
                    a.onclick = function () {
                        messageViewed(this.getAttribute("messageID"));
                        $(this).parent().next('li').remove(); // remove following divider <li>
                        $(this).parent().remove(); // remove message <li>
                        $(OVDM_messageCount).html(parseInt($(OVDM_messageCount).text()) - 1);
                    };
                    
                    var li = document.createElement('li');
                    li.appendChild(a);
                    ul.appendChild(li);
                    
                    var divider = document.createElement("li");
                    divider.setAttribute("class", "divider");

                    ul.appendChild(divider);
                }
                
                var i = document.createElement("i");
                i.setAttribute("class", "fa fa-angle-right");
                
                var s = document.createElement("strong");
                s.innerHTML = "Read All Messages ";
                s.appendChild(i);
                
                var a = document.createElement("a");
                a.setAttribute("class", "text-center");
                a.setAttribute("href", siteRoot + "config/messages");
                a.appendChild(s);
                
                var li = document.createElement("li");
                li.appendChild(a);
                ul.appendChild(li);
                
                $(OVDM_messagesUI).replaceWith(ul);
            }
            
            setTimeout(function () {
                updateRecentMessages(OVDM_messagesUI);
            }, 5000);
        });
    }
    
    function updateJobs(OVDM_jobsUI, OVDM_jobCount) {
        var getJobsURL = siteRoot + 'api/gearman/getJobs';
        $.getJSON(getJobsURL, function (data, status) {
            if (status === 'success' && data !== null) {

                var li = document.createElement("li");
                if (data.length === 0) {
                    var a = document.createElement("a");
                    a.setAttribute("class", "text-center");
                    a.setAttribute("href", "#");

                    var s = document.createElement("strong");
                    s.innerHTML = "No tasks currently running";
                    
                    a.appendChild(s);
                    li.appendChild(a);
                } else {
                    var i;
                    for (i = 0; i < data.length; i++) {
                        var progress = parseInt((data[i]['jobNumerator'] / data[i]['jobDenominator']) * 100, 10);

                        var sp2 = document.createElement("span");
                        sp2.setAttribute("class", "sr-only");
                        sp2.innerHTML = progress + "% Complete (success)";

                        var pb2 = document.createElement("div");
                        pb2.setAttribute("class", "progress-bar progress-bar-success");
                        pb2.setAttribute("role", "progressbar");
                        pb2.setAttribute("aria-valuemin", 0);
                        pb2.setAttribute("aria-valuenow", data[i]['jobNumerator']);
                        pb2.setAttribute("aria-valuemax", data[i]['jobDenominator']);
                        pb2.setAttribute("style", "width: " + progress + "%");
                        pb2.appendChild(sp2);
                        
                        var pb = document.createElement("div");
                        pb.setAttribute("class", "progress progress-striped active");
                        pb.appendChild(pb2);

                        var s = document.createElement("strong");
                        s.innerHTML = data[i]['jobName'];

                        var sp = document.createElement("span");
                        sp.setAttribute("class", "pull-right text-muted small");
                        sp.innerHTML = progress + "% Complete";

                        var p = document.createElement("p");
                        p.appendChild(s);
                        p.appendChild(sp);

                        var d = document.createElement("div");
                        d.appendChild(p);
                        d.appendChild(pb);

                        var a = document.createElement("a");
                        a.setAttribute("class", "OVDM_job");
                        a.setAttribute("jobID", data[i]['jobID']);
                        a.setAttribute("href", "#");
                        a.appendChild(d);
                        
                        li.appendChild(a);
                    }
                }

                $(OVDM_jobsUI).html(li);
                $(OVDM_jobCount).html(data.length);
            }
            setTimeout(function () {
                updateJobs(OVDM_jobsUI, OVDM_jobCount);
            }, 5000);
        });
    }
    
    function messageViewed(messageID) {
        var messageViewedURL = siteRoot + 'config/messages/viewedMessage/' + messageID;
        $.getJSON(messageViewedURL, function (data, status) {
            if (status === "success") {
//                updateMessages('#OVDM_messages', '#OVDM_messageCount');
            }
        });
    }
    
    // When document is ready...
    $(document).ready(function () {

        // If cookie is set, scroll to the position saved in the cookie.
        if ($.cookie("scrollDown") !== null) {
            $(document).scrollTop($.cookie("scrollDown"));
            $.removeCookie("scrollDown");
        }
    });
    
    // When a button is clicked...
    $('a').on("click", function () {
        // Set a cookie that holds the scroll position.
        $.cookie("scrollDown", $(document).scrollTop());
    });
    
    $('a.OVDM_message').on('click', function () {
        messageViewed($(this).attr('messageID'));
        $(this).parent().next('li').remove(); // remove following divider <li>
        $(this).parent().remove(); // remove message <li>
        $('#OVDM_messageCount').html(parseInt($('#OVDM_messageCount').text())-1); // decrement message count
    });
    
    updateSystemStatusPanel('#systemStatusPanel', '#systemStatus');
    updateCruiseSizePanel('#cruiseSizePanel', '#cruiseSize');
    updateFreeSpacePanel('#freeSpacePanel', '#freeSpace');
    updateRecentMessages('#OVDM_messages','#OVDM_messageCount');
    updateMessageCount('#OVDM_messageCount');
    updateJobs('#OVDM_jobs', '#OVDM_jobCount');

});