HTMLTextAreaElement.prototype.getCaretPosition = function () { //return the caret position of the textarea
    return this.selectionStart;
};
HTMLTextAreaElement.prototype.setCaretPosition = function (position) { //change the caret position of the textarea
    this.selectionStart = position;
    this.selectionEnd = position;
    this.focus();
};
HTMLTextAreaElement.prototype.hasSelection = function () { //if the textarea has selection then return true
    return this.selectionStart == this.selectionEnd;
};
HTMLTextAreaElement.prototype.getSelectedText = function () { //return the selection text
    return this.value.substring(this.selectionStart, this.selectionEnd);
};
HTMLTextAreaElement.prototype.setSelection = function (start, end) { //change the selection area of the textarea
    this.selectionStart = start;
    this.selectionEnd = end;
    this.focus();
};

var textarea = document.getElementsByTagName('textarea')[0]; 

textarea.onkeydown = function(event) {
    
    var oldPos = textarea.getCaretPosition();
    var newPos;
    
    if (event.keyCode == 9) { //TAB
        newPos = oldPos + 4;
        textarea.value = textarea.value.substring(0, oldPos) + "    " + textarea.value.substring(oldPos, textarea.value.length);
        textarea.setCaretPosition(newPos);
        return false;
    }

    else if(event.keyCode == 8){ //BACKSPACE
        if (textarea.value.substring(oldPos - 4, oldPos) == "    ") { //it's a tab space
            newPos = oldPos - 3;
            textarea.value = textarea.value.substring(0, oldPos - 3) + textarea.value.substring(oldPos, textarea.value.length);
            textarea.setCaretPosition(newPos);
        }
    }
    else if(event.keyCode == 37){ //LEFT
        if (textarea.value.substring(oldPos - 4, oldPos) == "    ") { //it's a tab space
            newPos = oldPos - 3;
            textarea.setCaretPosition(newPos);
        }    
    }
    else if(event.keyCode == 39){ //RIGHT
        if (textarea.value.substring(oldPos + 4, oldPos) == "    ") { //it's a tab space
            newPos = oldPos + 3;
            textarea.setCaretPosition(newPos);
        }
    } 
}