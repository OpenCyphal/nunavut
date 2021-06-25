function collapseOn(collapse) {
  collapse.classList.add("show");
}

function collapseOff(collapse) {
  collapse.classList.remove("show");
  linkFromCollapse(collapse).innerText = "+";
}

function showCollapse(collapse) {
  collapseOn(collapse);
  if (linkFromCollapse(collapse)) {
    linkFromCollapse(collapse).innerText = "-";
    if (!linkFromCollapse(collapse).parentNode.classList.contains("deprecated")) {
      linkFromCollapse(collapse).parentNode.classList.remove("d-none");
    }
  }

  if (collapse.parentNode != null && collapse.classList.contains("collapse")) {
    showCollapse(collapse.parentNode);
  }

  collapse.scrollIntoView({
    behavior: "smooth"
  });
}

function toggleCollapse(e, type_tag) {
  let collapse = document.querySelector(e.target.dataset.target);
  if (collapse.classList.contains("show")) {
    // collapse
    for (let el of collapse.querySelectorAll(".collapse.show")) {
      collapseOff(el);
    }
    collapseOff(collapse);
    e.target.innerText = "+";
  } else {
    // show
    showCollapse(collapse);
    e.target.innerText = "-";
  }

  scrollSidebar(type_tag);
}

function linkFromCollapse(collapse) {
  try {
    return collapse.previousSibling.previousSibling.querySelector("a");
  } catch (e) {
    return linkFromCollapse(collapse.parentNode.parentNode);
  }
}

function scrollSidebar(type) {
  let el = document.getElementById(`${type}_sidebar`);

  if (el.nodeName === "DIV") {
    showCollapse(el);
    linkFromCollapse(el).scrollIntoView({
      behavior: "smooth",
      inline: "start"
    });
  } else {
    showCollapse(el.parentNode.parentNode);
    el.scrollIntoView({
      behavior: "smooth"
    });
  }
}

function filterNamespaces(e) {
  console.log("yee", e.target.value)
  if (e.target.value === "") {
    for (let el of document.getElementById("namespaceinfo").querySelectorAll(".collapse")) {
        let lonk = linkFromCollapse(el);
        if (!lonk.parentNode.classList.contains("deprecated")) {
          lonk.parentNode.classList.remove("d-none");
        }

        if (el.classList.contains("type")) {
          collapseOff(el);
        } else {
          collapseOn(el);
        }
    }
  } else {
    for (let el of document.getElementById("namespaceinfo").querySelectorAll(".collapse")) {
      let lonk = linkFromCollapse(el);
      if (lonk.parentNode.innerText.toLowerCase().includes(e.target.value.toLowerCase())) {
        if (!el.classList.contains("nested")) {
          showCollapse(el);
        }

        if (!lonk.parentNode.classList.contains("deprecated")) {
          lonk.parentNode.classList.remove("d-none")
        }
      } else {
        el.classList.remove("show");
        collapseOff(el);
        if (!lonk.parentNode.classList.contains("deprecated") && !el.classList.contains("nested")) {
          lonk.parentNode.classList.add("d-none")
        }
      }
    }
  }
}
