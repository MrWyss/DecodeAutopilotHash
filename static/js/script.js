function searchinTable() {
  // Declare variables
  var input, filter, table, tr, td, i, txtValue;
  input = document.getElementById("searchinTable");
  filter = input.value.toUpperCase();
  table = document.getElementById("decodedtable");
  tr = table.getElementsByTagName("tr");

  // Loop through all table rows, and hide those who don't match the search query
  for (i = 0; i < tr.length; i++) {
    td = tr[i].getElementsByTagName("td")[0];
    if (td) {
      txtValue = td.textContent || td.innerText;
      if (txtValue.toUpperCase().indexOf(filter) > -1) {
        tr[i].style.display = "";
      } else {
        tr[i].style.display = "none";
      }
    }
  }
}
function copyPoshCommand() {
  // Get the text to be copied from the "POSHCommand" element
  var copyText = document.getElementById("POSHCommand");
  // Select the text field
  copyText.select();
  copyText.setSelectionRange(0, 99999)
  // Copy the text to the clipboard
  navigator.clipboard.writeText(copyText.value)
    .then(() => {
      // Flash the background of the "POSHCommand" element
      var poshElement = document.getElementById("POSHCommand");
      poshElement.style.backgroundColor = "#45a049";
      setTimeout(function() {
        poshElement.style.transition = "background-color 500ms linear";
        poshElement.style.backgroundColor = "";
      }, 1000);
    })
    .catch(err => {
      console.error('Failed to copy text: ', err);
    });
}

