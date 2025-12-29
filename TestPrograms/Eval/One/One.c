#include <stdio.h>

int MAGIC_CODE = 13;

int verify(int code);

int main() {
    int ID = 5;
    printf("Admin Portal.\n");
    printf("Fetching login profile...\n");
    printf("Currently logged in as ID=%d\n", ID);
    
    if (verify(ID)) {
        printf("Welcome, admin. Your flag is %s\n", "semurai{level_one_cle4red}");
    } else {
        printf("Access not granted. Invalid ID.\n");
    }
    return 0;
}

int verify(int code) {
    return code == MAGIC_CODE;
}
