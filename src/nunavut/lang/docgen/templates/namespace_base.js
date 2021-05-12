function collapseOn(collapse) {
  collapse.classList.add("show");
}

function collapseOff(collapse) {
  collapse.classList.remove("show");
}

function showCollapse(collapse) {
  collapseOn(collapse);
  if (linkFromCollapse(collapse)) {
    linkFromCollapse(collapse).innerText = "-";
  }

  if (collapse.parentNode != null && collapse.classList.contains("collapse")) {
    showCollapse(collapse.parentNode);
  }
}

function toggleCollapse(e) {
  let collapse = document.querySelector(e.target.dataset.target);
  console.log(collapse, e)
  if (collapse.classList.contains("show")) {
    // collapse
    for (let el of collapse.querySelectorAll(".collapse.show")) {
      collapseOff(el);
      linkFromCollapse(el).innerText = "+";
    }
    collapseOff(collapse);
    e.target.innerText = "+";
  } else {
    // show
    showCollapse(collapse);
    e.target.innerText = "-";
  }
}

function linkFromCollapse(collapse) {
  return collapse.previousSibling.previousSibling.querySelector("a");
}
