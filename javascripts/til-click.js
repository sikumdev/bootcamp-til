// 강조된 코드 줄을 클릭하면, 그 줄 바로 아래에 설명을 끼워 넣는다.
document.addEventListener("DOMContentLoaded", function() {
    document.querySelectorAll(".til-code").forEach(function(block) {
        var notes = block.querySelectorAll(".til-note");
        if (!notes.length) return;

        var codeEl = block.querySelector(".highlight code");
        if (!codeEl) return;

        // 이 블록의 줄 span 들 (__span-N-M). M이 줄 번호.
        var lineSpans = codeEl.querySelectorAll('span[id^="__span-"]');
        if (!lineSpans.length) return;

        // 줄번호 → 줄 span 매핑
        var byLine = {};
        lineSpans.forEach(function(sp) {
            var m = sp.id.match(/__span-\d+-(\d+)/);
            if (m) byLine[m[1]] = sp;
        });

        notes.forEach(function(note) {
            var lineNo = note.getAttribute("data-til-line");
            var span = byLine[lineNo];
            if (!span) return;

            // 클릭 대상은 그 줄 안의 강조 부분(.hll), 없으면 줄 전체
            var target = span.querySelector(".hll") || span;
            target.style.cursor = "pointer";
            target.title = "클릭하면 설명 보기";
            target.classList.add("til-clickable");

            // 설명 박스를 그 줄 span 바로 뒤에 옮겨 놓는다 (코드 안쪽)
            span.parentNode.insertBefore(note, span.nextSibling);

            target.addEventListener("click", function(e) {
                e.stopPropagation();
                if (note.hasAttribute("hidden")) note.removeAttribute("hidden");
                else note.setAttribute("hidden", "");
            });
        });
    });
});