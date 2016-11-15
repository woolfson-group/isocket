/**
 * Created by jackheal on 12/08/2016.
 */
$(".nav a").on("click", function(){
   $(".nav").find(".active").removeClass("active");
   $(this).parent().addClass("active");
});
