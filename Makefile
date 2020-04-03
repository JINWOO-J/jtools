REPO_HUB = jinwoo
NAME = jtools
VERSION = 0.6

ifdef version
VERSION = $(version)
endif

ifdef VERSION_ARG
VERSION = $(VERSION_ARG)
endif
ifdef REPO_HUB_ARG
REPO_HUB = $(REPO_HUB_ARG)
endif
ifeq ($(REPO_HUB_ARG),iconloop)
REPO_HUB = jinwoo
NAME= jtools
endif

define colorecho
      @tput setaf 6
      @echo $1
      @tput sgr0
endef

TAGNAME = $(VERSION)
NO_COLOR=\033[0m
OK_COLOR=\033[32m
ERROR_COLOR=\033[1;31m
WARN_COLOR=\033[93m

OK_STRING=$(OK_COLOR)[OK]$(NO_COLOR)
ERROR_STRING=$(ERROR_COLOR)[ERRORS]$(NO_COLOR)
WARN_STRING=$(WARN_COLOR)[WARNINGS]$(NO_COLOR)

.PHONY: all build push test tag_latest release ssh

all: build_slim builder
hub: push_hub tag_latest

print_version:
	@printf "$(OK_COLOR) VERSION-> $(VERSION)  REPO-> $(REPO_HUB)/$(NAME):$(TAGNAME) $(NO_COLOR) IS_LOCAL: $(IS_LOCAL) \n"

make_build_args:
	@$(shell printf "$(OK_COLOR) ----- Build Environment ----- \n $(NO_COLOR) \n" >&2)\
	   $(shell echo "" > BUILD_ARGS) \
		$(foreach V, \
			 $(sort $(.VARIABLES)), \
			 $(if  \
				 $(filter-out environment% default automatic, $(origin $V) ), \
				 	 $($V=$($V)) \
				 $(if $(filter-out "SHELL" "%_COLOR" "%_STRING" "MAKE%" "colorecho" ".DEFAULT_GOAL" "CURDIR", "$V" ),  \
					$(shell printf '$(OK_COLOR)  $V=$(WARN_COLOR)$($V) $(NO_COLOR) \n' >&2;) \
				 	$(shell echo "--build-arg $V=$($V)  " >> BUILD_ARGS)\
				  )\
			  )\
		 )

test:   make_build_args
		docker build --no-cache --rm=true -f dockerfile_test/Dockerfile  \
		$(shell cat BUILD_ARGS) \
		-t $(REPO_HUB)/$(NAME):$(TAGNAME) .

changeconfig: make_build_args
		@CONTAINER_ID=$(shell docker run -d $(REPO_HUB)/$(NAME):$(TAGNAME)) ;\
		 echo "COPY TO [$$CONTAINER_ID]" ;\
		 docker cp "src/." "$$CONTAINER_ID":/src/ ;\
		 docker exec -it "$$CONTAINER_ID" sh -c "echo `date +%Y-%m-%d:%H:%M:%S` > /.made_day" ;\
		 echo "COMMIT [$$CONTAINER_ID]" ;\
		 docker commit -m "Change the configure files `date`" "$$CONTAINER_ID" $(REPO_HUB)/$(NAME):$(TAGNAME) ;\
		 echo "STOP [$$CONTAINER_ID]" ;\
		 docker stop "$$CONTAINER_ID" ;\
		 echo "CLEAN UP [$$CONTAINER_ID]" ;\
		 docker rm "$$CONTAINER_ID"

#		-build-arg NAME=$(NAME) --build-arg APP_VERSION=$(VERSION) --build-arg DOWNLOAD_PACKAGE=$(DOWNLOAD_PACKAGE) \


builder : make_build_args
		docker build --no-cache --rm=true -f python_37/Dockerfile \
		$(shell cat BUILD_ARGS) --build-arg IS_BUILDER="true" \
		-t $(REPO_HUB)/$(NAME)-builder:$(TAGNAME) .

build_slim : make_build_args
		docker build --no-cache --rm=true -f python_37/Dockerfile \
		$(shell cat BUILD_ARGS) \
		-t $(REPO_HUB)/$(NAME):$(TAGNAME) .

push: print_version
		docker tag  $(NAME):$(VERSION) $(REPO_HUB)/$(NAME):$(TAGNAME)
		docker push $(REPO_HUB)/$(NAME):$(TAGNAME)

prod: print_version
		docker tag $(REPO_HUB)/$(NAME):$(TAGNAME)  $(REPO_HUB)/$(NAME):$(VERSION)
		docker push $(REPO_HUB)/$(NAME):$(VERSION)

push_hub: print_version
		#docker tag  $(NAME):$(VERSION) $(REPO_HUB)/$(NAME):$(VERSION)
		docker push $(REPO_HUB)/$(NAME):$(TAGNAME)

tag_latest: print_version
		docker tag  $(REPO_HUB)/$(NAME):$(TAGNAME) $(REPO_HUB)/$(NAME):latest
		docker push $(REPO_HUB)/$(NAME):latest

build_hub: print_version
		echo "TRIGGER_KEY" ${TRIGGERKEY}
		git add .
		git commit -m "$(NAME):$(VERSION) by Makefile"
		git tag -a "$(VERSION)" -m "$(VERSION) by Makefile"
		git push origin --tags
		curl -H "Content-Type: application/json" --data '{"build": true,"source_type": "Tag", "source_name": "$(VERSION)"}' -X POST https://registry.hub.docker.com/u/${REPO_HUB}/${NAME}/trigger/${TRIGGERKEY}/

bash: make_build_args print_version
		docker run  -it --net=host -v $(PWD)/:/mount -v $(PWD)/data:/data -e VERSION=$(TAGNAME) -v $(PWD)/src:/src --entrypoint /bin/bash --name $(NAME) --rm $(REPO_HUB)/$(NAME):$(TAGNAME)

score: make_build_args print_version
		docker run  -it --net=host -v $(PWD)/score:/score -v $(PWD)/data:/data -e VERSION=$(TAGNAME) -v $(PWD)/src:/src --entrypoint /bin/bash --name $(NAME) --rm iconloop/prep-node

dbash: make_build_args print_version
		docker run  -it --net=host -v $(PWD)/:/mount -v $(PWD)/data:/data -e VERSION=$(TAGNAME) -v $(PWD)/src:/src --entrypoint /bin/bash --name $(NAME) --rm $(REPO_HUB)/$(NAME)-builder:$(TAGNAME)

bbash: make_build_args print_version
		docker run  -it --net=host -v $(PWD)/:/mount -v $(PWD)/data:/data -v $(PWD)/build:/build -e VERSION=$(TAGNAME) -v $(PWD)/src:/src --entrypoint /bin/bash --name $(NAME)-builder --rm $(REPO_HUB)/$(NAME)-builder:$(TAGNAME)

list:
		@printf "$(OK_COLOR) Tag List - $(REPO_HUB)/$(NAME) $(NO_COLOR) \n"
		@curl -s  https://registry.hub.docker.com/v1/repositories/$(REPO_HUB)/$(NAME)/tags | jq --arg REPO "$(REPO_HUB)/$(NAME):" -r '.=("\($$REPO)"+.[].name)'
		$(call colorecho, "-- END --")

change_docker:
	sed -i '' "s/$(REPO_HUB)\/$(NAME).*/$(REPO_HUB)\/$(NAME):$(VERSION)/g" docker-compose.yml

gendocs:
	@$(shell ./makeMakeDown.sh)
#	@$(foreach image, prep-node, \
#	    echo "## $(image) docker setting" >README.md ;\
#		cat src/entrypoint.sh  | grep ^export | grep -v except| cut -d "=" -f 1 | sed 's/export//g' | sed 's/_/\\_/g' | sed -e 's/^/\|/' > text1 ;\
#		cat src/entrypoint.sh | grep ^export | grep -v except | cut -d "-" -f2 | cut -d "#" -f1 | sed -e 's/[[:space:]]\*$\//'| sed -E 's/-$|}$|"//g'|sed 's/_/\\_/g' > text2 ;\
#		cat src/entrypoint.sh | grep ^export | grep -v except| cut -d "-" -f2 | cut -d "#" -f2 | sed -e 's/[[:space:]]\*$\//'| sed -E 's/-$|}$|"//g' |sed 's/_/\\_/g'|sed -e 's/$\/\|/'  > text3 ;\
#		echo "| Environment variable |Default value|  Description|" >>README.md ;\
#		echo "|--------|--------|-------|"     >>README.md ;\
#		paste -d "|" text1  text2  text3 >>README.md ;\
#		rm -f text1  text2  text3 ;\
#     )
