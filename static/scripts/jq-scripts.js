$(document).ready(function() {

  // Check for click events on the navbar burger icon
  $(".navbar-burger").click(function() {
      // Toggle the "is-active" class on both the "navbar-burger" and the "navbar-menu"
      $(".navbar-burger").toggleClass("is-active");
      $(".navbar-menu").toggleClass("is-active");
  });

  $(".menu-burger").click(function() {
    // Toggle the "is-active" class on both the "navbar-burger" and the "navbar-menu"
    $(".menu-burger").toggleClass("is-active");
    $(".mobile-hidden").toggleClass("yesbile")
  });

  //graphite
  var loc = getUrlParameter('loc');

  $("#loadOverview").on("click", function() {
    $("#loading-dock").load("/graphite/views/overview.html");
    window.history.pushState('CardGen', 'CardGeb', '/graphite/');
  });

  $("#loadCardgen").on("click", function() {
    $("#loading-dock").load("/graphite/views/card.html");
    window.history.pushState('CardGen', 'CardGeb', '/graphite/?loc=cards');
  });

  if (loc == "cards"){
    $("#loading-dock").load("/graphite/views/card.html");
  }
  
  if (!loc){
    $("#loading-dock").load("/graphite/views/overview.html");
  }
});