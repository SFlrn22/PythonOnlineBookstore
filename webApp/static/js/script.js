document.querySelectorAll('.navbtn').forEach(link => {
    link.removeAttribute('aria-current', 'page')
    if(link.href === window.location.href){
        link.setAttribute('aria-current', 'page');
    }
})

let loadmorebtn = document.querySelector('#load-more');
let currentItem = 4;

loadmorebtn.onclick = () =>{
    let boxes = [...document.querySelectorAll('.container-prod')];
    try{
        for(var i = currentItem; i < currentItem+4; i++){
            boxes[i].style.display = 'inline-block';
        }
        currentItem+=4;
    } catch{
        loadmorebtn.style.display ='none';
    }
}


