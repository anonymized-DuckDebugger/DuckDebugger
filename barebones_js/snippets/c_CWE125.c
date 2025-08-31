int getValueFromArray(int *array, int len, int index) {
    int value;

    if (index < len) { //!! CWE125: out of bounds read. Proper check would be "index<len && index>=0" @@NUMS +2 @@KWORDS bound limit check verif @@TAGS CWE-125
        // get the value at the specified index of the array
        value = array[index];
    }
    // if array index is invalid then output error message
    // and return value indicating error
    else {
        printf("Value is: %d\n", array[index]); //!!CWE125: out of bounds read. Potential sensitive data exposure. @@KWORDS bound limit check verif @@NUMS 15 @@TAGS CWE-125
        value = -1;
    }

    return value;
}