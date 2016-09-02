$(document).ready(function() {
  
  // TOOLTIPS
  $.fn.tooltipped = function() {
    $(this).hover(function(event){
      markup = '<div id="memo-tooltip">' + 
        $( this ).attr('data-tooltip') + '</div>';
      that = $( this );
      that.append(markup);    
      tooltip = $( "#memo-tooltip" );
      tooltip.offset({
        left: (that.position().left + that.width()/2) - tooltip.outerWidth(true)/2,
        top: that.position().top - tooltip.outerHeight(true),
      });
    },
    function(event){    
      $('#memo-tooltip').remove();
    }); 
  };

  // FORM FOR ADDING LINKS
  $.fn.addForm = function() {
    var formObject = $(this); 
    var searchResults = $(this).find('.searchresults');

    linkToolsHtml = 
      '<div class="link-tools-container">\
          <div class="link-tools set text-right">\
            <a href="javascript:;" class="system button small view">View</a>\
            <a href="javascript:;" class="system button small expand">Expand</a>\
          </div>\
      </div>';     

    var submitForm = function() {         
      var activeTab = formObject.find(".active").data("tab");
      var editor = formObject.find(".formatted-text");
      formObject.find("input[name='text']").val(editor.html());
      var formData  = new FormData(formObject[0]);      
      if(['text','url','file','links'].indexOf(activeTab) < 0)
        return;                     
      send('POST', '/api/' + activeTab, formData, function(data){
        for (var i = 0; i < data.Result.length; i++) {
          $(data.Result[i].Link.Rendered).hide().insertBefore(formObject).slideToggle('fast');        
        };
      });
    };
    
    searchResults.on('click', 'div.link',function(event){
      event.stopPropagation();
      var id = urlToId($(this).data('path'));
      formObject.find('input[name="end_provider"]').val(id.Provider);
      formObject.find('input[name="end_id"]').val(id.Id);
      submitForm();
    });

    searchResults.on('click', '.button.view',function(event){
      event.stopPropagation();
      var row = $(this).closest('.link');
      var path = row.data("path");
      if(path != undefined && path != "")
        window.open(path, '_blank');        
    });

    searchResults.on('click', '.button.expand',function(event){ 
      event.stopPropagation();
      var row = $(this).closest('.link');                  
      $.ajax({
        url: "/api" + encodeURIComponent(row.data('path')) + "/links",
        dataType: "JSON",
        data: { mode: "templated" },      
        success: function(data) {         
          console.log(data);
          row.detach();          
          searchResults.empty(); 
          searchResults.append(row);
          for (var i = 0; i < data.Result.length; i++) {                 
            var result = $(data.Result[i].Rendered).hide().appendTo(searchResults).slideToggle();
            result.append(linkToolsHtml);            
          }
        }
      });
    });

    formObject.find('.searchinput').change(function(){ 
      searchResults.empty();       
      $.ajax({
        url: "/api/search",
        dataType: "JSON",
        data: { q: $( this ).val(), mode: "templated" },      
        success: function(data) {        
          console.log(data);
          for (var i = 0; i < data.Result.length; i++) {             
            var result = $(data.Result[i].Rendered).hide().appendTo(searchResults).slideToggle();
            result.append(linkToolsHtml);            
          }
        }
      });

    });
    
    $(this).find('.submitform').click(submitForm);        
    return this;
  };


  $('form.role-linkform').each(function(i,v){ $(this).addForm(); });
  $('.tooltipped').tooltipped();

  $('.links').on('click', '> .link', function(event){
    var path = $( this ).data("path");
    if(path != undefined && path != "")
        window.location = path;   
  });

  $('.links').on('click', '> .link a', function(event){
    event.stopPropagation();
  });

  $('.links').on('click', '.link .unlink', function(event){
    event.stopPropagation();    
    //data-action="send('DELETE', '/api/links/{{ link.Id }}')"
    var row = $(this).closest('.link');
    var id = row.data('id');
    confirm("Are you sure want to delete this link", function() {
      send('DELETE', '/api/links/' + id, null, function(){
        row.slideToggle('slow', function(){ $(this).remove()});
      });
    });  
  });

  $('.needconfirm').click(function(e) {
    e.preventDefault();
    that = $( this );
    target = $( this ).attr('href');
    title = $( this ).attr('title');
    text = "";
    if(title != undefined)
      text = "Are you sure want to " + title + "?";
    else
      text = "Are you sure?";
    if(target != undefined)
    {
      confirm(text, function() {
        window.location = target;
        eval(that.attr('data-action'));
      });    
    }
  });

  $('.tab-switch').click(function() {
    tabgroup = $( this ).data("tabgroup");
    target = $( this ).data("target");
    $('.'+tabgroup+'tab').removeClass('active').hide();

    tab = $('.'+tabgroup+'tab[data-tab="'+target+'"]');
    tab.addClass('active').show();    
    tab.find("*:input[type!=hidden]:first").first().focus();
    tab.find('.formatted-text').focus();
  });

  $('.toggle').click(function() {
    targetVal = $( this ).data("toggle");
    target = $(targetVal);    
    target.slideToggle('fast');
    target.find("*:input[type!=hidden]:first").first().focus();  
    target.find('.formatted-text').focus();    
  });  
});

var initEditor = function(selector) 
{
  return new MediumEditor(selector, {
    toolbar: {
      buttons: ['bold', 'italic', 'underline', 'anchor', 'h1', 'h2', 'h3', 'quote', 'orderedlist', 'unorderedlist'],
    },
    placeholder: { text: 'Type your text here...' },
    autoLink: true,
    paste: {
      cleanPastedHTML: true
    },
    anchorPreview: {        
        hideDelay: 200,
        // previewValueSelector: 'a'
    }
  });
};

function showNotification(message, type, buttonName, buttonCallback, timeout) { 
  message = typeof message !== 'undefined' ? message : 'Hello!';
  type = typeof type !== 'undefined' ? type : 'success';
  timeout = typeof timeout !== 'undefined' ? timeout : 3000;      
    
  if ($('#notification').length < 1) {
    markup = '<div id="notification" style="display:none;" class="information">\
                <span class="text">Hello!</span>&nbsp;\
                <span class="set text-right"></span>\
                <a class="close system button small" href="javascript:;">X</a>\
              </div>';
    $('body').append(markup);
  }
  
  $notification = $('#notification');
  if(buttonName != undefined) {
    $('#notification .set').html(
      "<a href='javascript:;' class='button small yes'>" + buttonName + "</a>" +
      "<a href='javascript:;' class='system button small no'>Cancel</a>"
    )    

    $('#notification .button.yes').click(function (e) {
      buttonCallback();
      e.preventDefault();
      $notification.slideUp();
    }); 

    $('#notification .button.no').click(function (e) {
      e.preventDefault();
      $notification.slideUp();
    }); 
  }
  
  // set the message
  $('#notification .text').text(message);
  
  // setup click event
  $('#notification a.close').click(function (e) {
    e.preventDefault();
    $notification.slideUp();
  });  
  
  $notification.removeClass().addClass(type);
  $notification.slideDown();  
  setTimeout(function() {
    $notification.slideUp();
  }, timeout);  
}

function notify(message, type, timeout) {
  showNotification(message, type, undefined, undefined, timeout);
}

function confirm(message, okCallback) {
  showNotification(message, "warn", "Yes", okCallback, 1000000);
}

function send(method, path, args, callback) { 
  $.ajax({
    url: path,
    type: method,
    data: args,
    async: true,
    dataType: 'JSON',
    success: function(data) {
      console.log(data);
      if(callback != undefined)
        callback(data);
      notify(data.StatusMessage, "success");          
    },
    error: function(err) {
      notify(data.StatusMessage, "error", 5000)
    },
    cache: false,
    contentType: false,      
    processData: false
  });
}

function urlToId(input) {
  var parts = input.split('/');
  return { 
    Provider: parts[1],
    Id: parts[2]
  };
}