function jaro(s1, s2) {
  let shorter, longer;

  [longer, shorter] = s1.length > s2.length ? [s1, s2] : [s2, s1];

  const matchingWindow = Math.floor(longer.length / 2) - 1;
  const shorterMatches = [];
  const longerMatches = [];

  for (let i = 0; i < shorter.length; i++) {
    let ch = shorter[i];
    const windowStart = Math.max(0, i - matchingWindow);
    const windowEnd = Math.min(i + matchingWindow + 1, longer.length);
    for (let j = windowStart; j < windowEnd; j++) {
      if (longerMatches[j] === undefined && ch === longer[j]) {        
        shorterMatches[i] = longerMatches[j] = ch;
        break;
      }
    }
  }

  const shorterMatchesString = shorterMatches.join("");
  const longerMatchesString = longerMatches.join("");
  const numMatches = shorterMatchesString.length;

  let transpositions = 0;
  for (let i = 0; i < shorterMatchesString.length; i++) {
    if (shorterMatchesString[i] !== longerMatchesString[i]) {
      transpositions++;
    }
  }

  return numMatches > 0
    ? (
        numMatches / shorter.length +
        numMatches / longer.length +
        (numMatches - Math.floor(transpositions / 2)) / numMatches
      ) / 3.0
    : 0;
}

function jaroWinkler (s1, s2, prefixScalingFactor = 0.2) {
  const jaroSimilarity = jaro(s1, s2);

  let commonPrefixLength = 0;
  for (let i = 0; i < s1.length; i++) {
    if (s1[i] === s2[i]) { commonPrefixLength++; } else { break; }
  }

  return jaroSimilarity +
    Math.min(commonPrefixLength, 4) *
    prefixScalingFactor *
    (1 - jaroSimilarity);
}

function memoize(fn){
  const cache = {};

  return (...args) => {
    const key = JSON.stringify(args);
    return cache[key] || (
      cache[key] = fn.apply(null, args)
    );
  };
}

class MissPlete {

  constructor({
    input,
    options,
    className,
    scoreFn = memoize(MissPlete.scoreFn),
    listItemFn = MissPlete.listItemFn
  }) {
    Object.assign(this, { input, options, className, scoreFn, listItemFn });

    this.scoredOptions = null;
    this.container = null;
    this.ul = null;
    this.highlightedIndex = -1;

    this.input.addEventListener('input', () => {
      if (this.input.value.length > 0) {
        this.scoredOptions = this.options
          .map(option => scoreFn(this.input.value, option))
          .sort((a, b) => b.score - a.score);
      } else {
        this.scoredOptions = [];
      }
      this.renderOptions();
      event.preventDefault();
      if (this.ul){
        this.changeHighlightedOption(0);
      }
    });

    this.input.addEventListener('keydown', event => {
      if (this.ul) {  // dropdown visible?
        switch (event.keyCode) {
          case 13: // Enter
            event.preventDefault();
            this.select();
            break;
          case 27:  // Esc
            if (this.ul){
              this.select();
            }
            break;
          case 40:  // Down arrow
            // Otherwise up arrow places the cursor at the beginning of the
            // field, and down arrow at the end
            event.preventDefault();
            this.changeHighlightedOption(
              this.highlightedIndex < this.ul.children.length - 1
              ? this.highlightedIndex + 1
              : 0
            );
            break;
          case 38:  // Up arrow
            event.preventDefault();
            this.changeHighlightedOption(
              this.highlightedIndex > 0
              ? this.highlightedIndex - 1
              : this.ul.children.length - 1
            );
            break;
        }
      }
    });

    this.input.addEventListener('blur', (event) => {
      if (this.ul){
        this.select()
      }
      this.removeDropdown(); 
      this.highlightedIndex = -1;

    });

    this.input.addEventListener('focus', (event) => {
      this.input.value = '';
    });
  }  // end constructor

  static scoreFn(inputValue, optionSynonyms) {
    let closestSynonym = null;
    for (let synonym of optionSynonyms) {
      let similarity = jaroWinkler(
        synonym.trim().toLowerCase(),
        inputValue.trim().toLowerCase()
      );
      if (closestSynonym === null || similarity > closestSynonym.similarity) {
        closestSynonym = { similarity, value: synonym };
        if (similarity === 1) { break; }
      }
    }
    return {
      score: closestSynonym.similarity,
      displayValue: optionSynonyms[0]
    };
  }

  static get MAX_ITEMS() {
    return 8;
  }

  static listItemFn(scoredOption, itemIndex) {
    const li = itemIndex > MissPlete.MAX_ITEMS
      ? null
      : document.createElement("li");
    li && li.appendChild(document.createTextNode(scoredOption.displayValue));
    return li;
  }

  getSiblingIndex(node) {
    let index = -1;
    let n = node;
    do {
      index++;
      n = n.previousElementSibling;
    } while (n);
    return index;
  }

  renderOptions() {
    const documentFragment = document.createDocumentFragment();

    this.scoredOptions.every((scoredOption, i) => {
      const listItem = this.listItemFn(scoredOption, i);
      listItem && documentFragment.appendChild(listItem);
      return !!listItem;
    });

    this.removeDropdown();
    this.highlightedIndex = -1;

    if (documentFragment.hasChildNodes()) {
      const newUl = document.createElement("ul");
      newUl.addEventListener('mouseover', event => {
        if (event.target.tagName === 'LI') {
          this.changeHighlightedOption(this.getSiblingIndex(event.target));
        }
      });

      newUl.addEventListener('mouseleave', () => {
        //this.changeHighlightedOption(-1);
      });

      //newUl.addEventListener('mousedown', event => event.preventDefault());

      newUl.addEventListener('click', event => {
        if (event.target.tagName === 'LI') {
          this.select();
        }
      });

      newUl.appendChild(documentFragment);

      // See CSS to understand why the <ul> has to be wrapped in a <div>
      const newContainer = document.createElement("div");
      newContainer.className = this.className;
      newContainer.appendChild(newUl);

      // Inserts the dropdown just after the <input> element
      this.input.parentNode.insertBefore(newContainer, this.input.nextSibling);
      this.container = newContainer;
      this.ul = newUl;
    }
  }

  changeHighlightedOption(newHighlightedIndex) {
    if (newHighlightedIndex >= -1 &&
        newHighlightedIndex < this.ul.children.length)
    {
      // If any option already selected, then unselect it
      if (this.highlightedIndex !== -1) {
        this.ul.children[this.highlightedIndex].classList.remove("highlight");
      }

      this.highlightedIndex = newHighlightedIndex;

      if (this.highlightedIndex !== -1) {
        this.ul.children[this.highlightedIndex].classList.add("highlight");
      }

    }
  }

  select() {
    if (this.highlightedIndex !== -1) {
      this.input.value = this.scoredOptions[this.highlightedIndex].displayValue;
      this.removeDropdown();
      this.input.blur();
    }
  }

  removeDropdown() {
    this.container && this.container.remove();
    this.container = null;
    this.ul = null;
  }

}

