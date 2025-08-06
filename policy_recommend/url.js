//        boardSeq, menuSeq
// 기관소식: 47 7100
// 타기관소식: 2 282

// 실행시 링크 생성 후 새 창으로 이동
function get_url(boardSeq=47, menuSeq=7100, conSeq=466575){
    // 1. <form> 엘리먼트를 동적으로 생성합니다.
    const form = document.createElement('form');

    // 2. Form의 속성을 설정합니다.
    form.setAttribute('method', 'POST'); // 전송 방식: POST
    form.setAttribute('action', 'https://www.liveinkorea.kr/portal/KOR/board/mlbs/boardView.do'); // 제출 URL
    form.setAttribute('target', '_blank'); // 새 창(_blank)에서 열리도록 설정

    // 3. 전송할 데이터를 객체 형태로 정의합니다.
    const formData = {
        boardSeq: boardSeq,
        menuSeq: menuSeq,
        conSeq: conSeq
    };

    // 4. formData 객체의 모든 키-값 쌍에 대해 <input> 엘리먼트를 생성하고 form에 추가합니다.
    for (const key in formData) {
        if (Object.prototype.hasOwnProperty.call(formData, key)) {
            const dataInput = document.createElement('input');
            dataInput.setAttribute('type', 'hidden');
            dataInput.setAttribute('name', key); // name은 객체의 키(key)로 설정
            dataInput.setAttribute('value', formData[key]); // value는 객체의 값(value)으로 설정
            form.appendChild(dataInput);
        }
    }

    // 5. 완성된 <form>을 현재 문서의 <body> 맨 끝에 추가합니다.
    document.body.appendChild(form);

    form.submit();

    document.body.removeChild(form);
}
