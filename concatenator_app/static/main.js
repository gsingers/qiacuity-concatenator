function select_all(element_name) {
  var ele = document.getElementsByName(element_name);
  for (var i = 0; i < ele.length; i++) {
    if (ele[i].type === 'checkbox')
      ele[i].checked = true;
  }
}

function deSelect_all(element_name) {
  var ele = document.getElementsByName(element_name);
  for (var i = 0; i < ele.length; i++) {
    if (ele[i].type === 'checkbox')
      ele[i].checked = false;

  }
}

// Flip checked to it's opposite
function invert_all(element_name) {
  var ele = document.getElementsByName(element_name);
  for (var i = 0; i < ele.length; i++) {
    if (ele[i].type === 'checkbox')
      ele[i].checked = ! ele[i].checked ;

  }
}

function toggle_button(element_id){
  var ele = document.getElementById(element_id);
  if (ele.type === 'button') {

    ele.disabled = !ele.disabled;
  }
}

function set_button(element_id, disabled){
  var ele = document.getElementById(element_id);
  if (ele.type === 'button') {
    ele.disabled = disabled;
  }
}